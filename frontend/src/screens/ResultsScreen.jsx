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

export default function ResultsScreen({ analysisMode, result }) {
  const traits = Object.entries(result).sort(
    ([, left], [, right]) => right.weight - left.weight,
  )
  const totalWeight = traits.reduce((sum, [, trait]) => sum + trait.weight, 0)

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
          {analysisMode === 'mock' ? 'Mock Data' : 'Gemini Response'} • Total
          Weight {formatPercent(totalWeight)}
        </p>
      </motion.div>

      <div className="w-full max-w-5xl">
        <BubblesView traits={traits} traitLabels={TRAIT_LABELS} />
      </div>
    </main>
  )
}
