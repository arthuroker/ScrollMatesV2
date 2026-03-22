import { motion } from 'motion/react'
import BubblesView from '../components/BubblesView'

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

function formatScore(score) {
  return score.toFixed(3)
}

export default function ResultsScreen({ analysisMode, result }) {
  const traits = Object.entries(result.traits).sort(
    ([, left], [, right]) => right.weight - left.weight,
  )
  const totalWeight = traits.reduce((sum, [, trait]) => sum + trait.weight, 0)
  const matches = result.matches || []

  return (
    <main className="box-border min-h-screen w-full max-w-full overflow-x-clip flex flex-col items-center px-8 pt-34 pb-32">
      <motion.div
        className="text-center mb-4"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="font-headline text-3xl font-extrabold text-brand mb-1">
          Trait Summary
        </h2>
        <p className="mt-3 font-label text-[10px] uppercase tracking-[0.25em] text-brand/45">
          {analysisMode === 'mock' ? 'Mock Data' : 'Current Profile'} • Total
          Weight {formatPercent(totalWeight)}
        </p>
      </motion.div>

      <div className="w-full max-w-5xl">
        <BubblesView traits={traits} traitLabels={TRAIT_LABELS} />
      </div>

      <section className="mt-10 w-full max-w-3xl animate-fade-up">
        <div className="mb-4 text-center">
          <h3 className="font-headline text-2xl font-extrabold text-brand">
            Weekly Matches
          </h3>
          <p className="mt-2 font-label text-[10px] uppercase tracking-[0.25em] text-brand/45">
            Latest completed drop
          </p>
        </div>

        {matches.length === 0 ? (
          <div className="glass rounded-3xl px-6 py-5 text-center">
            <p className="font-headline text-lg font-bold text-brand">
              No match drop yet
            </p>
            <p className="mt-2 text-sm text-brand/65">
              Your profile is ready. Weekly matches will appear here after the next completed run.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {matches.map((match) => (
              <article key={`${match.week_start}-${match.rank}`} className="glass rounded-3xl px-6 py-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/45">
                      Rank {match.rank}
                    </p>
                    <p className="mt-1 font-headline text-xl font-bold text-brand break-all">
                      {match.matched_user_id}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/45">
                      Similarity
                    </p>
                    <p className="mt-1 font-headline text-xl font-bold text-brand">
                      {formatScore(match.similarity_score)}
                    </p>
                  </div>
                </div>

                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {Object.entries(match.score_breakdown).map(([key, value]) => (
                    <div key={key} className="rounded-2xl bg-white/35 px-4 py-3">
                      <p className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/45">
                        {TRAIT_LABELS[key] || key}
                      </p>
                      <p className="mt-1 font-headline text-sm font-bold text-brand">
                        {formatScore(value)}
                      </p>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
