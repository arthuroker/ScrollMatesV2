const STAGES_ORDER = [
  'queued',
  'persisting_upload',
  'validating_video',
  'uploading_to_gemini',
  'waiting_for_gemini',
  'generating_summary',
]

const STAGE_CONFIG = {
  queued: {
    label: 'In the queue',
    sublabel: 'Preparing to process your video',
  },
  persisting_upload: {
    label: 'Saving recording',
    sublabel: 'Writing your video to storage',
  },
  validating_video: {
    label: 'Validating video',
    sublabel: 'Checking format and duration',
  },
  uploading_to_gemini: {
    label: 'Uploading video',
    sublabel: 'Preparing for analysis',
  },
  waiting_for_gemini: {
    label: 'Analyzing',
    sublabel: 'Processing your recording',
  },
  generating_summary: {
    label: 'Almost there',
    sublabel: 'Crafting your scroll personality',
  },
}

function QueuedAnimation() {
  return (
    <div className="flex items-center gap-3 h-16">
      <div className="w-3 h-3 rounded-full bg-brand/50 animate-queue-1" />
      <div className="w-3.5 h-3.5 rounded-full bg-brand/40 animate-queue-2" />
      <div className="w-3 h-3 rounded-full bg-brand/30 animate-queue-3" />
    </div>
  )
}

function PersistingUploadAnimation() {
  return (
    <div className="relative w-16 h-16">
      <svg className="w-full h-full" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="26" fill="none" stroke="#542822" strokeWidth="2" opacity="0.1" />
        <circle
          cx="32" cy="32" r="26"
          fill="none" stroke="#542822" strokeWidth="2.5"
          strokeDasharray="163"
          strokeLinecap="round"
          opacity="0.45"
          className="animate-persist-ring"
          style={{ transformOrigin: 'center', transform: 'rotate(-90deg)' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className="material-symbols-outlined text-brand/45 text-2xl"
          style={{ fontVariationSettings: '"FILL" 1' }}
        >
          save
        </span>
      </div>
    </div>
  )
}

function ValidatingVideoAnimation() {
  return (
    <div className="relative w-16 h-16">
      <svg className="w-full h-full" viewBox="0 0 64 64">
        <rect x="12" y="16" width="40" height="32" rx="4" fill="none" stroke="#542822" strokeWidth="1.5" opacity="0.15" />
        <polygon points="27,24 27,40 40,32" fill="#542822" opacity="0.2" />
        <rect
          x="12" y="31" width="40" height="2" rx="1"
          fill="#542822" opacity="0.45"
          className="animate-scan-line"
        />
      </svg>
      <div className="absolute top-2 right-2">
        <span
          className="material-symbols-outlined text-brand/40 text-base animate-check-pop"
          style={{ fontVariationSettings: '"FILL" 1' }}
        >
          check_circle
        </span>
      </div>
    </div>
  )
}

function UploadingToGeminiAnimation() {
  return (
    <div className="relative w-16 h-16">
      <svg className="w-full h-full" viewBox="0 0 64 64">
        <path
          d="M18 42 C12 42 8 37.5 8 32.5 C8 27.5 12 23.5 17.5 23.5 C18.5 18 23.5 14 30 14 C37.5 14 43 18.5 44 23.5 C49.5 23.5 54 27.5 54 32.5 C54 37.5 49.5 42 44 42"
          fill="none" stroke="#542822" strokeWidth="1.5" opacity="0.2" strokeLinecap="round"
        />
        <circle cx="25" cy="50" r="2" fill="#542822" opacity="0.5" className="animate-particle-1" />
        <circle cx="32" cy="54" r="1.5" fill="#855049" opacity="0.4" className="animate-particle-2" />
        <circle cx="39" cy="52" r="2" fill="#542822" opacity="0.45" className="animate-particle-3" />
        <circle cx="28" cy="56" r="1" fill="#855049" opacity="0.3" className="animate-particle-4" />
        <circle cx="36" cy="48" r="1.5" fill="#542822" opacity="0.35" className="animate-particle-5" />
      </svg>
    </div>
  )
}

function WaitingForGeminiAnimation() {
  return (
    <div className="relative w-16 h-16">
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-2.5 h-2.5 rounded-full bg-brand/25 animate-center-pulse" />
      </div>
      <div className="absolute inset-2 animate-orbit" style={{ animationDuration: '3s' }}>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2.5 h-2.5 rounded-full bg-brand/50" />
      </div>
      <div className="absolute inset-2 animate-orbit" style={{ animationDuration: '3s', animationDelay: '-1s' }}>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-secondary/40" />
      </div>
      <div className="absolute inset-2 animate-orbit" style={{ animationDuration: '3s', animationDelay: '-2s' }}>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-brand/30" />
      </div>
    </div>
  )
}

function GeneratingSummaryAnimation() {
  return (
    <div className="relative w-16 h-16 flex items-center justify-center">
      <span
        className="material-symbols-outlined text-brand/40 text-4xl animate-gen-icon"
        style={{ fontVariationSettings: '"FILL" 1' }}
      >
        auto_awesome
      </span>
      <div className="absolute top-0.5 right-0 w-1.5 h-1.5 rounded-full bg-brand/50 animate-sparkle-1" />
      <div className="absolute bottom-1 left-0.5 w-1 h-1 rounded-full bg-secondary/40 animate-sparkle-2" />
      <div className="absolute top-2 left-1 w-1 h-1 rounded-full bg-brand/30 animate-sparkle-3" />
      <div className="absolute bottom-0 right-2 w-1.5 h-1.5 rounded-full bg-secondary/35 animate-sparkle-4" />
    </div>
  )
}

function StageAnimation({ stage }) {
  switch (stage) {
    case 'queued': return <QueuedAnimation />
    case 'persisting_upload': return <PersistingUploadAnimation />
    case 'validating_video': return <ValidatingVideoAnimation />
    case 'uploading_to_gemini': return <UploadingToGeminiAnimation />
    case 'waiting_for_gemini': return <WaitingForGeminiAnimation />
    case 'generating_summary': return <GeneratingSummaryAnimation />
    default: return <QueuedAnimation />
  }
}

function StageProgress({ stage }) {
  const currentIndex = STAGES_ORDER.indexOf(stage)

  return (
    <div className="flex gap-2">
      {STAGES_ORDER.map((s, i) => (
        <div
          key={s}
          className={`h-1.5 rounded-full transition-all duration-500 ${
            i <= currentIndex
              ? 'bg-brand/40 w-3'
              : 'bg-brand/10 w-1.5'
          }`}
        />
      ))}
    </div>
  )
}

export default function AnalyzingScreen({ stage }) {
  const config = STAGE_CONFIG[stage] || STAGE_CONFIG.queued

  return (
    <main className="box-border min-h-screen w-full max-w-full overflow-x-clip flex flex-col items-center justify-center px-8">
      <div key={stage} className="flex flex-col items-center animate-stage-enter">
        <div className="mb-6">
          <StageAnimation stage={stage} />
        </div>

        <p className="font-body text-sm text-brand/70 font-medium">
          {config.label}
        </p>
        <p className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/30 mt-1.5">
          {config.sublabel}
        </p>
      </div>

      <div className="mt-10">
        <StageProgress stage={stage} />
      </div>
    </main>
  )
}
