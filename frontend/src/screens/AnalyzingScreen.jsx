import { useEffect, useState } from 'react'

const STEP_SETS = {
  mock: [
    { icon: 'data_object', label: 'Loading local sample traits...' },
    { icon: 'dashboard', label: 'Formatting trait cards...' },
    { icon: 'check_circle', label: 'Preparing summary view...' },
  ],
  real: [
    { icon: 'upload_file', label: 'Uploading recording...' },
    { icon: 'movie_filter', label: 'Validating video limits...' },
    { icon: 'psychology', label: 'Gemini is inferring traits...' },
    { icon: 'analytics', label: 'Rendering structured JSON...' },
  ],
}

export default function AnalyzingScreen({ analysisMode, fileName }) {
  const steps = STEP_SETS[analysisMode]
  const [step, setStep] = useState(0)

  useEffect(() => {
    const interval = window.setInterval(() => {
      setStep((currentStep) => {
        if (currentStep < steps.length - 1) {
          return currentStep + 1
        }
        return 0
      })
    }, 1100)

    return () => window.clearInterval(interval)
  }, [steps.length])

  const progress = ((step + 1) / steps.length) * 100

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-8 pt-20 pb-28">
      <div className="relative w-40 h-40 mb-10 flex items-center justify-center animate-fade-up">
        <div className="absolute inset-0 rounded-full border-2 border-brand/10" />
        <svg className="absolute inset-0 w-full h-full animate-spin" style={{ animationDuration: '3s' }} viewBox="0 0 160 160">
          <circle
            cx="80"
            cy="80"
            r="76"
            fill="none"
            stroke="#542822"
            strokeWidth="2.5"
            strokeDasharray="120 360"
            strokeLinecap="round"
            opacity="0.3"
          />
        </svg>
        <div className="glass-strong w-24 h-24 rounded-full flex items-center justify-center animate-scroll-pulse">
          <span className="material-symbols-outlined text-4xl text-brand" style={{ fontVariationSettings: "'FILL' 1" }}>
            {steps[step].icon}
          </span>
        </div>
      </div>

      <div className="text-center mb-8 animate-fade-up" style={{ animationDelay: '0.15s' }}>
        <h2 className="font-headline text-2xl font-extrabold text-brand mb-2">
          {analysisMode === 'mock' ? 'Loading Mock Summary' : 'Analyzing With Gemini'}
        </h2>
        <p className="font-body text-secondary text-sm tracking-wide mb-1">{fileName}</p>
        <div className="flex items-center justify-center gap-1 mt-3">
          <span className="font-label text-xs text-brand/70">{steps[step].label}</span>
          <span className="flex gap-0.5 ml-1">
            <span className="w-1 h-1 rounded-full bg-brand/50 animate-dot-1" />
            <span className="w-1 h-1 rounded-full bg-brand/50 animate-dot-2" />
            <span className="w-1 h-1 rounded-full bg-brand/50 animate-dot-3" />
          </span>
        </div>
      </div>

      <div className="w-full max-w-xs animate-fade-up" style={{ animationDelay: '0.3s' }}>
        <div className="w-full h-1.5 rounded-full bg-brand/10 overflow-hidden">
          <div
            className="h-full rounded-full bg-brand/60 transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-center font-label text-[10px] uppercase tracking-widest text-brand/40 mt-3">
          {analysisMode === 'mock' ? 'Mock mode' : 'Real mode'}
        </p>
      </div>

      <div className="mt-8 w-full max-w-xs space-y-2 animate-fade-up" style={{ animationDelay: '0.4s' }}>
        {steps.map((currentStep, index) => (
          <div
            key={currentStep.label}
            className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-500 ${
              index < step
                ? 'opacity-100'
                : index === step
                  ? 'opacity-100 glass'
                  : 'opacity-30'
            }`}
          >
            <span className="material-symbols-outlined text-sm text-brand" style={{ fontVariationSettings: index <= step ? "'FILL' 1" : "'FILL' 0" }}>
              {index < step ? 'check_circle' : index === step ? currentStep.icon : 'radio_button_unchecked'}
            </span>
            <span className="font-label text-xs text-brand/80">{currentStep.label}</span>
          </div>
        ))}
      </div>
    </main>
  )
}
