const TRAIT_LABELS = {
  relational_orientation: 'Relational Orientation',
  creativity: 'Creativity',
  intellectualism: 'Intellectualism',
  humor: 'Humor',
  interests: 'Interests',
  cultural_identity: 'Cultural Identity',
  political_orientation: 'Political Orientation',
}

function formatPercent(weight) {
  return `${Math.round(weight * 100)}%`
}

function TraitCard({ description, name, weight, delay }) {
  return (
    <article className="glass rounded-2xl p-5 animate-fade-up" style={{ animationDelay: `${delay}s` }}>
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <p className="font-headline text-lg font-bold text-brand">{name}</p>
          <p className="mt-2 font-body text-sm leading-6 text-brand/75">{description}</p>
        </div>
        <div className="shrink-0 rounded-full bg-brand/10 px-3 py-1">
          <span className="font-label text-xs uppercase tracking-[0.2em] text-brand">{formatPercent(weight)}</span>
        </div>
      </div>
      <div className="h-2 rounded-full bg-brand/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand/60 via-brand to-secondary transition-all duration-700 ease-out"
          style={{ width: `${Math.max(weight * 100, 6)}%` }}
        />
      </div>
    </article>
  )
}

export default function ResultsScreen({ analysisMode, fileName, onReset, result }) {
  const traits = Object.entries(result).sort(([, left], [, right]) => right.weight - left.weight)
  const totalWeight = traits.reduce((sum, [, trait]) => sum + trait.weight, 0)

  return (
    <main className="min-h-screen flex flex-col items-center px-8 pt-24 pb-32">
      <div className="text-center mb-8 animate-fade-up">
        <h2 className="font-headline text-3xl font-extrabold text-brand mb-1">
          Trait Summary
        </h2>
        <p className="font-body text-secondary text-sm tracking-wide">{fileName}</p>
        <p className="mt-3 font-label text-[10px] uppercase tracking-[0.25em] text-brand/45">
          {analysisMode === 'mock' ? 'Mock Data' : 'Gemini Response'} • Total Weight {formatPercent(totalWeight)}
        </p>
      </div>

      <div className="w-full max-w-sm space-y-4 mb-10">
        {traits.map(([key, trait], index) => (
          <TraitCard
            key={key}
            delay={0.15 + index * 0.08}
            description={trait.description}
            name={TRAIT_LABELS[key] || key}
            weight={trait.weight}
          />
        ))}
      </div>

      <div className="w-full max-w-sm space-y-3 animate-fade-up" style={{ animationDelay: '0.6s' }}>
        <button
          type="button"
          className="w-full py-4 px-6 rounded-lg text-on-primary font-headline font-bold text-center transition-all duration-300 active:scale-[0.98] bg-brand/85 backdrop-blur-md shadow-lg shadow-brand/15 border border-brand/20"
          onClick={onReset}
        >
          Analyze Another
        </button>
      </div>
    </main>
  )
}
