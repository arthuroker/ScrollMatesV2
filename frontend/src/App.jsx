import { useState } from 'react'
import Header from './components/Header'
import BottomNav from './components/BottomNav'
import UploadScreen from './screens/UploadScreen'
import AnalyzingScreen from './screens/AnalyzingScreen'
import ResultsScreen from './screens/ResultsScreen'
import { summarizeVideo } from './lib/api'
import { MOCK_SUMMARY, MOCK_SUMMARY_DELAY_MS } from './lib/mockSummary'

function App() {
  const [screen, setScreen] = useState('upload')
  const [file, setFile] = useState(null)
  const [analysisMode, setAnalysisMode] = useState('mock')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    if (!file) {
      return
    }

    setError(null)
    setScreen('analyzing')

    try {
      let nextResult

      if (analysisMode === 'mock') {
        await new Promise((resolve) => window.setTimeout(resolve, MOCK_SUMMARY_DELAY_MS))
        nextResult = MOCK_SUMMARY
      } else {
        nextResult = await summarizeVideo(file)
      }

      setResult(nextResult)
      setScreen('results')
    } catch (nextError) {
      setError(nextError.message || 'Unable to analyze this recording right now.')
      setScreen('upload')
    }
  }

  const handleReset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setScreen('upload')
  }

  return (
    <div className="font-body text-on-surface antialiased overflow-hidden">
      <Header />

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
        <AnalyzingScreen
          analysisMode={analysisMode}
          fileName={file?.name || 'video.mp4'}
        />
      )}

      {screen === 'results' && result && (
        <ResultsScreen
          analysisMode={analysisMode}
          fileName={file?.name || 'video.mp4'}
          onReset={handleReset}
          result={result}
        />
      )}

      <BottomNav />
    </div>
  )
}

export default App
