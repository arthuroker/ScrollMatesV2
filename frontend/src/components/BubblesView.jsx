import { useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence, LayoutGroup } from 'motion/react'

const PALETTE = [
  '#542822',
  '#855049',
  '#a17060',
  '#6e4a3a',
  '#4c7c87',
  '#7a9e6b',
  '#c49070',
]

function wrapLabel(label) {
  const words = label.split(' ')
  if (words.length <= 1) return [label]
  const mid = Math.ceil(words.length / 2)
  return [words.slice(0, mid).join(' '), words.slice(mid).join(' ')]
}

function packCircles(items) {
  const circles = items.map((c) => ({ ...c }))

  // Sort largest first, place at center
  circles.sort((a, b) => b.r - a.r)
  circles[0].x = 0
  circles[0].y = 0

  // Arrange the rest in a ring
  const ring = circles.slice(1)
  ring.forEach((c, i) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * i) / ring.length
    const dist = circles[0].r + c.r + 8
    c.x = dist * Math.cos(angle)
    c.y = dist * Math.sin(angle)
  })

  // Resolve overlaps with simple force iterations
  for (let iter = 0; iter < 60; iter++) {
    for (let i = 0; i < circles.length; i++) {
      for (let j = i + 1; j < circles.length; j++) {
        const dx = circles[j].x - circles[i].x
        const dy = circles[j].y - circles[i].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        const minDist = circles[i].r + circles[j].r + 5
        if (dist < minDist && dist > 0) {
          const overlap = (minDist - dist) / 2
          const nx = dx / dist
          const ny = dy / dist
          circles[i].x -= overlap * nx
          circles[i].y -= overlap * ny
          circles[j].x += overlap * nx
          circles[j].y += overlap * ny
        }
      }
    }
    // Gentle pull toward center
    circles.forEach((c) => {
      c.x *= 0.995
      c.y *= 0.995
    })
  }

  return circles
}

export default function BubblesView({ traits, traitLabels }) {
  const [selected, setSelected] = useState(null)
  const [layoutExpanded, setLayoutExpanded] = useState(false)
  const selectedRef = useRef(null)

  const minR = 55
  const maxR = 95

  const circles = useMemo(() => {
    const mw = Math.max(...traits.map(([, t]) => t.weight))
    const items = traits.map(([key, trait], i) => ({
      key,
      trait,
      label: traitLabels[key] || key,
      r: minR + (maxR - minR) * (trait.weight / mw),
      color: PALETTE[i % PALETTE.length],
      x: 0,
      y: 0,
    }))
    return packCircles(items)
  }, [traits, traitLabels])

  // Compute viewBox from packed positions
  const pad = 60
  const bounds = circles.reduce(
    (b, c) => ({
      minX: Math.min(b.minX, c.x - c.r),
      maxX: Math.max(b.maxX, c.x + c.r),
      minY: Math.min(b.minY, c.y - c.r),
      maxY: Math.max(b.maxY, c.y + c.r),
    }),
    { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity },
  )
  const vx = bounds.minX - pad
  const vy = bounds.minY - pad
  const vw = bounds.maxX - bounds.minX + pad * 2
  const vh = bounds.maxY - bounds.minY + pad * 2

  const selectedTrait = selected ? traits.find(([k]) => k === selected) : null
  const selectedCircle = selected ? circles.find((c) => c.key === selected) : null
  const hasSelection = Boolean(selectedTrait && selectedCircle)

  return (
    <motion.div
      className="flex flex-col items-center w-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.4 }}
    >
      <LayoutGroup>
      <div
        className={`mx-auto w-full ${
          layoutExpanded
            ? 'flex max-w-4xl flex-col items-center gap-6 md:grid md:grid-cols-[minmax(0,1fr)_minmax(14rem,16rem)] md:items-center md:gap-10'
            : 'flex justify-center'
        }`}
      >
        <motion.div
          layout
          className="w-full max-w-xl flex-shrink-0"
          transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <svg
            viewBox={`${vx} ${vy} ${vw} ${vh}`}
            preserveAspectRatio="xMidYMid meet"
            className="block aspect-square h-auto w-full overflow-visible"
          >
            {circles.map((c, i) => {
              const lines = wrapLabel(c.label)
              const fontSize = Math.max(8, Math.min(11, c.r / 5.5))
              const lh = fontSize + 3
              const isSelected = selected === c.key
              const dimmed = selected !== null && !isSelected

              return (
                <motion.g
                  key={c.key}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{
                    scale: 1,
                    opacity: dimmed ? 0.45 : 1,
                  }}
                  transition={{
                    delay: 0.05 + i * 0.07,
                    duration: 0.5,
                    type: 'spring',
                    stiffness: 180,
                    damping: 14,
                    opacity: { duration: 0.3, delay: 0 },
                  }}
                  style={{ transformOrigin: `${c.x}px ${c.y}px` }}
                  onClick={() => {
                    const next = selected === c.key ? null : c.key
                    selectedRef.current = next
                    setSelected(next)
                    if (next) setLayoutExpanded(true)
                  }}
                  className="cursor-pointer"
                >
                  <circle
                    cx={c.x}
                    cy={c.y}
                    r={c.r}
                    fill={c.color}
                    opacity={isSelected ? 1 : 0.82}
                    stroke={isSelected ? '#fff' : 'none'}
                    strokeWidth={isSelected ? 3 : 0}
                  />
                  {/* Trait name (wrapped) */}
                  {lines.map((line, li) => (
                    <text
                      key={li}
                      x={c.x}
                      y={c.y + (li - (lines.length - 1) / 2) * lh - 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      style={{ fontSize: `${fontSize}px` }}
                      className="font-headline font-bold pointer-events-none"
                      fill="white"
                    >
                      {line}
                    </text>
                  ))}
                  {/* Percentage */}
                  <text
                    x={c.x}
                    y={c.y + ((lines.length - 1) / 2) * lh + lh - 2}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    style={{ fontSize: `${fontSize - 1}px` }}
                    className="font-label pointer-events-none"
                    fill="rgba(255,255,255,0.7)"
                  >
                    {Math.round(c.trait.weight * 100)}%
                  </text>
                </motion.g>
              )
            })}
          </svg>
        </motion.div>

        <AnimatePresence mode="wait" onExitComplete={() => { if (!selectedRef.current) setLayoutExpanded(false) }}>
          {hasSelection ? (
            <motion.div
              key={selected}
              className="w-full max-w-sm md:max-w-xs min-h-[10rem]"
              initial={{ opacity: 0, filter: 'blur(6px)' }}
              animate={{ opacity: 1, filter: 'blur(0px)' }}
              exit={{ opacity: 0, filter: 'blur(6px)' }}
              transition={{
                duration: 0.25,
                ease: [0.25, 0.1, 0.25, 1],
              }}
            >
              <div className="flex flex-col items-start">
                {/* Accent bar + title */}
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: selectedCircle.color }}
                  />
                  <h4 className="font-headline text-lg font-bold text-brand leading-tight">
                    {traitLabels[selected] || selected}
                  </h4>
                </div>

                {/* Weight bar */}
                <div className="w-full mb-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-label text-[10px] uppercase tracking-[0.15em] text-brand/40">
                      Weight
                    </span>
                    <span className="font-headline text-sm font-bold text-brand/70">
                      {Math.round(selectedTrait[1].weight * 100)}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-brand/8 overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: selectedCircle.color }}
                      initial={{ width: 0 }}
                      animate={{ width: `${selectedTrait[1].weight * 100}%` }}
                      transition={{
                        type: 'spring',
                        stiffness: 100,
                        damping: 16,
                        delay: 0.1,
                      }}
                    />
                  </div>
                </div>

                {/* Description */}
                <div className="glass-subtle rounded-xl px-4 py-3">
                  <p className="font-body text-sm text-brand/70 leading-relaxed">
                    {selectedTrait[1].description}
                  </p>
                </div>
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
      </LayoutGroup>

      {/* Hint when nothing selected */}
      <div className="h-1 flex items-center justify-center">
        <AnimatePresence>
          {!selected && (
            <motion.p
              className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/25"
              initial={{ opacity: 0 }}
              animate={{
                opacity: 1,
                transition: { delay: 0.6, duration: 0.4 },
              }}
              exit={{ opacity: 0, transition: { duration: 0.15 } }}
            >
              Tap a bubble to see details
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
