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

const JOB_STAGE_TO_UI_STAGE = {
  upload: 'persisting_upload',
  gemini_analysis: 'waiting_for_gemini',
  embedding: 'generating_summary',
  done: 'generating_summary',
}

function toUiStage(stage) {
  return JOB_STAGE_TO_UI_STAGE[stage] || 'queued'
}

function App() {
  const [screen, setScreen] = useState('landing')
  const [file, setFile] = useState(null)
  const [analysisMode, setAnalysisMode] = useState('mock')
  const [isAuthBypassed, setIsAuthBypassed] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [session, setSession] = useState(null)
  const [stage, setStage] = useState('queued')
  const analyzeIdRef = useRef(0)

  useEffect(() => {
    if (!isSupabaseConfigured) {
      return
    }

    let mounted = true

    getSession()
      .then((nextSession) => {
        if (!mounted) return
        setSession(nextSession)
        if (nextSession) {
          setScreen('upload')
        }
      })
      .catch(() => {})

    const { data } = onAuthStateChange((nextSession) => {
      if (!mounted) return
      setSession(nextSession)
      if (nextSession) {
        setIsAuthBypassed(false)
        setScreen((current) => (
          current === 'landing' || current === 'signin'
            ? 'upload'
            : current
        ))
      } else if (!isAuthBypassed) {
        setScreen('landing')
      }
    })

    return () => {
      mounted = false
      data.subscription.unsubscribe()
    }
  }, [isAuthBypassed])

  const handleUnauthorized = async () => {
    await signOut().catch(() => {})
    window.alert('Your session expired. Sign in again to continue.')
    setScreen('signin')
  }

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
        const kickoff = await uploadVideo(file)
        if (cancelled()) return
        setStage('persisting_upload')

        let status = {
          id: kickoff.job_id,
          status: 'pending',
          stage: 'upload',
        }

        while (status.status !== 'completed' && status.status !== 'failed') {
          await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS))
          if (cancelled()) return
          status = await getJobStatus(kickoff.job_id)
          if (cancelled()) return
          setStage(toUiStage(status.stage))
        }

        if (status.status === 'failed') {
          throw new Error(status.error_message || 'Analysis failed.')
        }

        const [profile] = await Promise.all([
          getProfile(),
          getMatches().catch(() => []),
        ])

        if (cancelled()) return
        setResult(profile.personality_json)
        setScreen('results')
      }
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
    analyzeIdRef.current++
    setFile(null)
    setResult(null)
    setError(null)
    setStage('queued')
    setScreen(session || isAuthBypassed ? 'upload' : 'landing')
  }

  const handleSignOut = async () => {
    setIsAuthBypassed(false)
    handleReset()
    await signOut().catch(() => {})
    setScreen('landing')
  }

  const handleSignIn = async ({ mode, email, password }) => {
    try {
      if (!isSupabaseConfigured) {
        throw new Error('Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY before signing in.')
      }

      if (mode === 'signup') {
        const data = await signUpWithPassword({ email, password })
        if (!data.session) {
          window.alert('Account created. If email confirmation is enabled, confirm your email before signing in.')
          return
        }
      } else {
        await signInWithPassword({ email, password })
      }
      setIsAuthBypassed(false)
      setScreen('upload')
    } catch (nextError) {
      window.alert(nextError.message || 'Unable to sign in right now.')
    }
  }

  const handleBypassAuth = () => {
    setIsAuthBypassed(true)
    setAnalysisMode('mock')
    setError(null)
    setScreen('upload')
  }

  const handleGetStarted = () => {
    setError(null)
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
        <SignInScreen onBypassAuth={handleBypassAuth} onSignIn={handleSignIn} />
      )}

      {screen === 'upload' && (
        <UploadScreen
          analysisMode={analysisMode}
          allowRealAnalysis={!isAuthBypassed}
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
