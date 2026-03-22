const STAGES_ORDER = [
  'upload',
  'gemini_analysis',
  'embedding',
]

const STAGE_CONFIG = {
  upload: {
    label: 'Saving recording',
    sublabel: 'Creating your profile job',
    icon: 'upload_file',
  },
  gemini_analysis: {
    label: 'Analyzing scroll',
    sublabel: 'Gemini is building your personality map',
    icon: 'auto_awesome',
  },
  embedding: {
    label: 'Computing matches',
    sublabel: 'Embedding traits for this week’s drop',
    icon: 'bubble_chart',
  },
}

function StageProgress({ stage }) {
  const currentIndex = STAGES_ORDER.indexOf(stage)

  return (
    <div className="flex gap-2">
      {STAGES_ORDER.map((stageName, index) => (
        <div
          key={stageName}
          className={`h-1.5 rounded-full transition-all duration-500 ${
            index <= currentIndex
              ? 'bg-brand/40 w-8'
              : 'bg-brand/10 w-3'
          }`}
        />
      ))}
    </div>
  )
}

export default function AnalyzingScreen({ stage }) {
  const config = STAGE_CONFIG[stage] || STAGE_CONFIG.upload

  return (
    <main className="box-border min-h-screen w-full max-w-full overflow-x-clip flex flex-col items-center justify-center px-8">
      <div key={stage} className="flex flex-col items-center animate-stage-enter">
        <div className="glass-strong mb-6 flex h-20 w-20 items-center justify-center rounded-full shadow-lg shadow-brand/10">
          <span
            className="material-symbols-outlined text-brand/50 text-4xl animate-center-pulse"
            style={{ fontVariationSettings: '"FILL" 1' }}
          >
            {config.icon}
          </span>
        </div>

        <p className="font-body text-sm text-brand/70 font-medium">
          {config.label}
        </p>
        <p className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/30 mt-1.5 text-center">
          {config.sublabel}
        </p>
      </div>

      <div className="mt-10">
        <StageProgress stage={stage} />
      </div>
    </main>
  )
}
