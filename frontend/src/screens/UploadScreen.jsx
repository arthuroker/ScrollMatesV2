import { useRef, useState } from 'react'

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const ANALYSIS_OPTIONS = [
  {
    value: 'mock',
    label: 'Mock Data',
    description: 'Uses the local sample trait summary.',
  },
  {
    value: 'real',
    label: 'Real Gemini',
    description: 'Uploads the recording to FastAPI and Gemini.',
  },
]

export default function UploadScreen({
  analysisMode,
  error,
  file,
  onAnalyze,
  setAnalysisMode,
  setFile,
}) {
  const inputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const handleFile = (nextFile) => {
    if (nextFile) setFile(nextFile)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0])
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-8 pt-20 pb-28">
      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        className="hidden"
        onChange={(e) => {
          if (e.target.files.length) handleFile(e.target.files[0])
          e.target.value = ''
        }}
      />

      <div className="w-full max-w-sm mb-12 ml-[10%] animate-fade-up" style={{ animationDelay: '0.25s' }}>
        <h2 className="font-headline text-4xl font-extrabold leading-tight tracking-tight text-brand">
          Upload
          <br />
          Recording
        </h2>
        <p className="mt-4 font-body text-secondary text-sm tracking-wide">
          Choose mock mode for local sample data or real mode to summarize the uploaded video.
        </p>
      </div>

      <div className="w-full max-w-sm mb-6 animate-fade-up" style={{ animationDelay: '0.35s' }}>
        <p className="font-headline text-xs font-bold uppercase tracking-widest text-brand/50 mb-3 px-1">
          Analysis Mode
        </p>
        <div className="space-y-3">
          {ANALYSIS_OPTIONS.map((option) => {
            const isSelected = option.value === analysisMode

            return (
              <button
                key={option.value}
                type="button"
                className={`w-full rounded-2xl border px-4 py-4 text-left transition-all duration-300 ${
                  isSelected
                    ? 'glass border-brand/25 shadow-lg shadow-brand/10'
                    : 'bg-white/35 border-white/50 hover:bg-white/45'
                }`}
                onClick={() => setAnalysisMode(option.value)}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-headline text-base font-bold text-brand">{option.label}</p>
                    <p className="mt-1 font-label text-xs tracking-wide text-brand/65">{option.description}</p>
                  </div>
                  <span
                    className={`material-symbols-outlined text-xl ${
                      isSelected ? 'text-brand' : 'text-brand/30'
                    }`}
                    style={{ fontVariationSettings: isSelected ? "'FILL' 1" : "'FILL' 0" }}
                  >
                    radio_button_checked
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      </div>

      <div className="relative w-full max-w-sm flex flex-col items-center">
        {!file && (
          <div
            className={`drop-zone group relative flex items-center justify-center w-64 h-64 mb-8 cursor-pointer animate-fade-up ${dragOver ? 'drag-over' : ''}`}
            style={{ animationDelay: '0.4s' }}
            onClick={() => inputRef.current?.click()}
            onDragLeave={() => setDragOver(false)}
            onDragOver={(e) => {
              e.preventDefault()
              setDragOver(true)
            }}
            onDrop={handleDrop}
          >
            <div className="absolute inset-0 rounded-full bg-brand/[0.06] animate-soft-ping" />
            <div className="absolute inset-4 rounded-full bg-brand/[0.06]" />
            <div className="drop-circle glass-strong relative z-10 w-48 h-48 rounded-full flex flex-col items-center justify-center transition-transform duration-500">
              <span className="material-symbols-outlined text-5xl mb-2 text-brand">upload_file</span>
              <span className="font-label text-[10px] uppercase tracking-widest text-brand/60">Drop here</span>
            </div>
          </div>
        )}

        {file && (
          <div className="glass w-full flex items-center gap-4 px-5 py-4 rounded-xl mb-4 animate-fade-up">
            <div className="w-11 h-11 rounded-xl bg-brand flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-white text-xl">play_arrow</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-label text-sm font-medium text-brand truncate">{file.name}</p>
              <p className="font-label text-xs text-secondary mt-0.5">{formatSize(file.size)}</p>
            </div>
            <button
              type="button"
              className="w-8 h-8 rounded-full bg-brand/10 flex items-center justify-center hover:bg-brand hover:text-white transition-colors group/rm"
              onClick={() => {
                setFile(null)
                if (inputRef.current) {
                  inputRef.current.value = ''
                }
              }}
            >
              <span className="material-symbols-outlined text-lg text-brand group-hover/rm:text-white">close</span>
            </button>
          </div>
        )}

        {error && (
          <div className="w-full mb-4 rounded-2xl border border-error/20 bg-error/8 px-4 py-3 animate-fade-up">
            <p className="font-label text-xs uppercase tracking-[0.2em] text-error/70">Analysis Failed</p>
            <p className="mt-1 text-sm text-brand/80">{error}</p>
          </div>
        )}

        <div className="w-full space-y-4 animate-fade-up" style={{ animationDelay: '0.55s' }}>
          {file && (
            <button
              type="button"
              className="w-full py-4 px-6 rounded-lg text-on-primary font-headline font-bold text-center transition-all duration-300 active:scale-[0.98] bg-brand/85 backdrop-blur-md shadow-lg shadow-brand/15 border border-brand/20 animate-fade-up"
              onClick={onAnalyze}
            >
              {analysisMode === 'mock' ? 'Use Mock Summary' : 'Summarize With Gemini'}
            </button>
          )}
          <button
            type="button"
            className="w-full text-secondary font-label text-xs uppercase tracking-[0.2em] hover:opacity-70 transition-opacity text-center py-2"
            onClick={() => inputRef.current?.click()}
          >
            Browse Files
          </button>
        </div>
      </div>

      <div className="mt-16 w-16 h-px bg-outline-variant/30 animate-fade-up" style={{ animationDelay: '0.55s' }} />
    </main>
  )
}
