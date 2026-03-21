import { useEffect, useState } from 'react'

const LABELS = {
  mock: ['Loading sample traits', 'Formatting cards', 'Almost done'],
  real: ['Uploading recording', 'Analyzing with Gemini', 'Rendering results'],
}

export default function AnalyzingScreen({ analysisMode, fileName }) {
  const labels = LABELS[analysisMode]
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const interval = window.setInterval(() => {
      setIndex((i) => (i + 1) % labels.length)
    }, 2000)
    return () => window.clearInterval(interval)
  }, [labels.length])

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-8">
      <div className="relative w-10 h-10 mb-8 animate-fade-up">
        <div className="absolute inset-0 rounded-full border-2 border-brand/10" />
        <svg className="absolute inset-0 w-full h-full animate-spin" style={{ animationDuration: '1.8s' }} viewBox="0 0 40 40">
          <circle
            cx="20"
            cy="20"
            r="18"
            fill="none"
            stroke="#542822"
            strokeWidth="2"
            strokeDasharray="28 85"
            strokeLinecap="round"
            opacity="0.45"
          />
        </svg>
      </div>

      <p className="font-body text-sm text-brand/70 animate-fade-up" style={{ animationDelay: '0.1s' }}>
        {labels[index]}
      </p>
      <p className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/30 mt-2 animate-fade-up" style={{ animationDelay: '0.2s' }}>
        {fileName}
      </p>
    </main>
  )
}
