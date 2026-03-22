import { useEffect, useRef, useState } from 'react'
import Header from './components/Header'
import LandingV1 from './landing/LandingV1'
import SignInScreen from './screens/SignInScreen'
import UploadScreen from './screens/UploadScreen'
import AnalyzingScreen from './screens/AnalyzingScreen'
import ResultsScreen from './screens/ResultsScreen'
import { ApiError, getJobStatus, getMatches, getProfile, uploadVideo } from './lib/api'
import { MOCK_STAGES, MOCK_SUMMARY } from './lib/mockSummary'
import {
  getSession,
  isSupabaseConfigured,
  onAuthStateChange,
  signInWithPassword,
  signOut,
  signUpWithPassword,
} from './lib/supabase'

const POLL_INTERVAL_MS = 2000

function App() {
  const [screen, setScreen] = useState('landing')
  const [file, setFile] = useState(null)
  const [analysisMode, setAnalysisMode] = useState('mock')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [authError, setAuthError] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)
  const [stage, setStage] = useState('upload')
  const [session, setSession] = useState(null)
  const analyzeIdRef = useRef(0)

  const devMode = !isSupabaseConfigured

  useEffect(() => {
    if (devMode) {
      setAnalysisMode('mock')
      setScreen('upload')
      return
    }

    let mounted = true

    getSession()
      .then((nextSession) => {
        if (!mounted) return
        setSession(nextSession)
        setScreen(nextSession ? 'upload' : 'landing')
      })
      .catch((nextError) => {
        if (!mounted) return
        setAuthError(nextError.message || 'Unable to load the current session.')
        setScreen('signin')
      })

    const { data } = onAuthStateChange((nextSession) => {
      if (!mounted) return
      setSession(nextSession)
      if (nextSession) {
        setAuthError(null)
        setScreen((currentScreen) => (currentScreen === 'landing' || currentScreen === 'signin' ? 'upload' : currentScreen))
      } else {
        analyzeIdRef.current += 1
        setFile(null)
        setResult(null)
        setError(null)
        setStage('upload')
        setScreen('landing')
      }
    })

    return () => {
      mounted = false
      data.subscription.unsubscribe()
    }
  }, [devMode])

  const handleUnauthorized = async () => {
    await signOut().catch(() => {})
    setAuthError('Your session expired. Sign in again to continue.')
    setScreen('signin')
  }

  const handleAnalyze = async () => {
    if (!file) return

    const currentId = ++analyzeIdRef.current
    const cancelled = () => analyzeIdRef.current !== currentId

    setError(null)
    setScreen('analyzing')
    setStage('upload')

    try {
      if (analysisMode === 'mock') {
        for (const { stage: nextStage, duration } of MOCK_STAGES) {
          if (cancelled()) return
          setStage(nextStage)
          await new Promise((resolve) => setTimeout(resolve, duration))
        }
        if (cancelled()) return
        setResult({
          traits: MOCK_SUMMARY,
          matches: [],
        })
        setScreen('results')
        return
      }

      const kickoff = await uploadVideo(file)
      if (cancelled()) return

      let status = {
        id: kickoff.job_id,
        status: 'pending',
        stage: 'upload',
      }

      while (status.status !== 'completed' && status.status !== 'failed') {
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))
        if (cancelled()) return
        status = await getJobStatus(kickoff.job_id)
        if (cancelled()) return
        setStage(status.stage || 'upload')
      }

      if (status.status === 'failed') {
        throw new ApiError(status.error_message || 'Analysis failed.', {
          status: 400,
          code: status.error_code,
        })
      }

      const [profile, matches] = await Promise.all([getProfile(), getMatches()])
      if (cancelled()) return
      setResult({
        traits: profile.personality_json,
        weights: profile.weights,
        matches,
      })
      setScreen('results')
    } catch (nextError) {
      if (cancelled()) return
      if (nextError instanceof ApiError && nextError.status === 401) {
        await handleUnauthorized()
        return
      }
      setError(nextError.message || 'Unable to analyze this recording right now.')
      setScreen('upload')
    }
  }

  const handleReset = () => {
    analyzeIdRef.current += 1
    setFile(null)
    setResult(null)
    setError(null)
    setStage('upload')
    setScreen(session || devMode ? 'upload' : 'landing')
  }

  const handleSignOut = async () => {
    handleReset()
    await signOut().catch((nextError) => {
      setAuthError(nextError.message || 'Unable to sign out.')
    })
  }

  const handleAuthSubmit = async ({ mode, email, password }) => {
    setAuthError(null)
    setAuthLoading(true)

    try {
      if (mode === 'signup') {
        await signUpWithPassword({ email, password })
      } else {
        await signInWithPassword({ email, password })
      }
    } catch (nextError) {
      setAuthError(nextError.message || 'Authentication failed.')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleGetStarted = () => {
    setAuthError(null)
    setScreen('signin')
  }

  return (
    <div className="box-border w-full max-w-full overflow-x-clip font-body text-on-surface antialiased">
      {screen !== 'landing' && screen !== 'signin' && (
        <Header onReset={handleReset} onSignOut={session ? handleSignOut : null} />
      )}

      {screen === 'landing' && (
        <LandingV1 onGetStarted={handleGetStarted} />
      )}

      {screen === 'signin' && (
        <SignInScreen
          error={authError}
          loading={authLoading}
          onSubmit={handleAuthSubmit}
        />
      )}

      {screen === 'upload' && (
        <UploadScreen
          analysisMode={analysisMode}
          devMode={devMode}
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
