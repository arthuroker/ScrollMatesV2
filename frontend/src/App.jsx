import { useRef, useState } from 'react'
import Header from './components/Header'
import LandingV1 from './landing/LandingV1'
import SignInScreen from './screens/SignInScreen'
import UploadScreen from './screens/UploadScreen'
import AnalyzingScreen from './screens/AnalyzingScreen'
import ResultsScreen from './screens/ResultsScreen'
import { getJobStatus, summarizeVideo } from './lib/api'
import { MOCK_STAGES, MOCK_SUMMARY } from './lib/mockSummary'

const POLL_INTERVAL_MS = 2000

function App() {
  const [screen, setScreen] = useState('landing')
  const [file, setFile] = useState(null)
  const [analysisMode, setAnalysisMode] = useState('mock')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [stage, setStage] = useState('queued')
  const analyzeIdRef = useRef(0)

  const handleAnalyze = async () => {
    if (!file) return

    const currentId = ++analyzeIdRef.current
    const cancelled = () => analyzeIdRef.current !== currentId

    setError(null)
    setScreen('analyzing')
    setStage('queued')

    try {
      if (analysisMode === 'mock') {
        for (const { stage: s, duration } of MOCK_STAGES) {
          if (cancelled()) return
          setStage(s)
          await new Promise((r) => setTimeout(r, duration))
        }
        if (cancelled()) return
        setResult(MOCK_SUMMARY)
        setScreen('results')
      } else {
        const kickoff = await summarizeVideo(file)
        if (cancelled()) return
        setStage(kickoff.stage || 'persisting_upload')

        const jobId = kickoff.job_id
        let status = kickoff

        while (status.status !== 'completed' && status.status !== 'failed') {
          await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
          if (cancelled()) return
          status = await getJobStatus(jobId)
          if (cancelled()) return
          setStage(status.stage)
        }

        if (status.status === 'failed') {
          throw new Error(status.error?.message || 'Analysis failed.')
        }

        setResult(status.summary)
        setScreen('results')
      }
    } catch (nextError) {
      if (cancelled()) return
      setError(nextError.message || 'Unable to analyze this recording right now.')
      setScreen('upload')
    }
  }

  const handleReset = () => {
    analyzeIdRef.current++
    setFile(null)
    setResult(null)
    setError(null)
    setStage('queued')
    setScreen('upload')
  }

  const handleSignOut = () => {
    handleReset()
    setScreen('landing')
  }

  const handleSignIn = () => {
    setScreen('upload')
  }

  const handleGetStarted = () => {
    setScreen('signin')
  }

  return (
    <div className="box-border w-full max-w-full overflow-x-clip font-body text-on-surface antialiased">
      {screen !== 'landing' && screen !== 'signin' && (
        <Header onReset={handleReset} onSignOut={handleSignOut} />
      )}

      {screen === 'landing' && (
        <LandingV1 onGetStarted={handleGetStarted} />
      )}

      {screen === 'signin' && (
        <SignInScreen onSignIn={handleSignIn} />
      )}

      {screen === 'upload' && (
        <UploadScreen
          analysisMode={analysisMode}
          error={error}
          file={file}
          onAnalyze={handleAnalyze}
          setAnalysisMode={setAnalysisMode}
          setFile={setFile}
        />
      )}

      {screen === 'analyzing' && (
        <AnalyzingScreen stage={stage} />
      )}

      {screen === 'results' && result && (
        <ResultsScreen
          analysisMode={analysisMode}
          result={result}
        />
      )}
    </div>
  )
}

export default App
