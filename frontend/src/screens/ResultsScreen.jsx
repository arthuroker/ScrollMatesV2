import { useCallback, useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'

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

function TraitCard({ description, name, weight, index }) {
  return (
    <motion.article
      className="glass rounded-2xl p-5 shrink-0 w-56 flex flex-col justify-between"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 + index * 0.08, duration: 0.5, ease: 'easeOut' }}
    >
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <p className="font-headline text-base font-bold text-brand leading-tight">{name}</p>
          <span className="shrink-0 font-label text-xs uppercase tracking-[0.15em] text-brand/60">{formatPercent(weight)}</span>
        </div>
        <p className="font-body text-xs leading-5 text-brand/70">{description}</p>
      </div>
      <div className="h-1.5 rounded-full bg-brand/10 overflow-hidden mt-4">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-brand/60 via-brand to-secondary"
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(weight * 100, 6)}%` }}
          transition={{ delay: 0.4 + index * 0.08, duration: 0.7, ease: 'easeOut' }}
        />
      </div>
    </motion.article>
  )
}

function ScrollArrow() {
  return (
    <motion.svg
      className="w-5 h-5 text-brand/50"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2.5}
      animate={{ x: [0, 5, 0] }}
      transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </motion.svg>
  )
}

export default function ResultsScreen({ analysisMode, result }) {
  const traits = Object.entries(result).sort(([, left], [, right]) => right.weight - left.weight)
  const totalWeight = traits.reduce((sum, [, trait]) => sum + trait.weight, 0)
  const scrollRef = useRef(null)
  const [canScroll, setCanScroll] = useState({ left: false, right: false })

  const checkScroll = useCallback(() => {
    const el = scrollRef.current
    if (!el) return
    setCanScroll({
      left: el.scrollLeft > 2,
      right: el.scrollLeft + el.clientWidth < el.scrollWidth - 2,
    })
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    // Delay initial check so cards have rendered
    const timer = setTimeout(checkScroll, 100)
    el.addEventListener('scroll', checkScroll, { passive: true })
    window.addEventListener('resize', checkScroll)
    return () => {
      clearTimeout(timer)
      el.removeEventListener('scroll', checkScroll)
      window.removeEventListener('resize', checkScroll)
    }
  }, [checkScroll])

  return (
    <main className="min-h-screen flex flex-col items-center px-8 pt-44 pb-32">
      <motion.div
        className="text-center mb-8"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="font-headline text-3xl font-extrabold text-brand mb-1">
          Trait Summary
        </h2>

        <p className="mt-3 font-label text-[10px] uppercase tracking-[0.25em] text-brand/45">
          {analysisMode === 'mock' ? 'Mock Data' : 'Gemini Response'} • Total Weight {formatPercent(totalWeight)}
        </p>
      </motion.div>

      <div className="relative w-full max-w-5xl mb-10">
        {/* Left fade edge */}
        <AnimatePresence>
          {canScroll.left && (
            <motion.div
              className="pointer-events-none absolute left-0 top-0 bottom-4 w-12 z-10 rounded-l-2xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              style={{
                background: 'linear-gradient(to right, rgba(254,242,232,0.95), transparent)',
              }}
            />
          )}
        </AnimatePresence>

        {/* Right fade edge + animated arrow */}
        <AnimatePresence>
          {canScroll.right && (
            <motion.div
              className="pointer-events-none absolute right-0 top-0 bottom-4 w-16 z-10 flex items-center justify-end pr-2 rounded-r-2xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              style={{
                background: 'linear-gradient(to left, rgba(254,242,232,0.95), transparent)',
              }}
            >
              <ScrollArrow />
            </motion.div>
          )}
        </AnimatePresence>

        <div
          ref={scrollRef}
          className="w-full overflow-x-auto pb-4"
        >
          <div className="flex gap-4" style={{ minWidth: 'min-content' }}>
            {traits.map(([key, trait], index) => (
              <TraitCard
                key={key}
                index={index}
                description={trait.description}
                name={TRAIT_LABELS[key] || key}
                weight={trait.weight}
              />
            ))}
          </div>
        </div>

        {/* Scroll hint text */}
        <AnimatePresence>
          {canScroll.right && (
            <motion.p
              className="text-center mt-2 font-label text-[10px] uppercase tracking-[0.2em] text-brand/30"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 4 }}
              transition={{ duration: 0.3, delay: 0.8 }}
            >
              Swipe to see more →
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}
