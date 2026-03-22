import { motion } from "motion/react"

/**
 * V1 — "Warm Editorial"
 * Big capybara hero, oversized Manrope wordmark, warm cream palette,
 * floating ambient particles, soft glow behind logo.
 */

const PARTICLES = Array.from({ length: 6 }, (_, i) => ({
  id: i,
  size: 3 + Math.random() * 4,
  x: 15 + Math.random() * 70,
  y: 10 + Math.random() * 80,
  duration: 12 + Math.random() * 10,
  delay: Math.random() * 6,
  opacity: 0.12 + Math.random() * 0.12,
}))

export default function LandingV1({ onGetStarted }) {
  return (
    <section
      className="relative min-h-screen w-full overflow-x-clip bg-[#fef2e8]"
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {/* Layered warm gradient washes */}
        <div
          className="absolute inset-0"
          style={{
            background: `
              radial-gradient(ellipse at 20% 10%, rgba(84,40,34,0.08) 0%, transparent 50%),
              radial-gradient(ellipse at 80% 85%, rgba(50,99,110,0.05) 0%, transparent 45%),
              radial-gradient(ellipse at 55% 50%, rgba(133,80,73,0.04) 0%, transparent 55%)
            `,
          }}
        />

        {/* Floating ambient particles */}
        {PARTICLES.map((p) => (
          <motion.div
            key={p.id}
            className="absolute rounded-full"
            style={{
              width: p.size,
              height: p.size,
              left: `${p.x}%`,
              top: `${p.y}%`,
              background: p.id % 2 === 0 ? "#855049" : "#32636e",
              opacity: 0,
            }}
            animate={{
              opacity: [0, p.opacity, 0],
              y: [0, -30, -60],
              x: [0, p.id % 2 === 0 ? 10 : -10, 0],
            }}
            transition={{
              duration: p.duration,
              delay: p.delay,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center justify-center px-4 py-16 text-center sm:px-6 lg:px-8">
        <div className="w-full max-w-xl flex flex-col items-center text-center">
          {/* Capybara with glow halo */}
          <motion.div
            className="relative mb-8"
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.9, ease: [0.25, 0.1, 0.25, 1] }}
          >
            {/* Soft pulsing glow behind logo */}
            <motion.div
              className="absolute inset-[-28px] rounded-full"
              style={{
                background:
                  "radial-gradient(circle, rgba(133,80,73,0.12) 0%, rgba(84,40,34,0.04) 50%, transparent 70%)",
              }}
              animate={{ scale: [1, 1.08, 1], opacity: [0.6, 1, 0.6] }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
            <img
              src="/capybara-cropped.png"
              alt="ScrollMates"
              className="w-28 h-28 relative z-10"
            />
          </motion.div>

          {/* Giant wordmark */}
          <motion.h1
            className="font-headline font-extrabold tracking-[-0.035em] text-[#542822] leading-[0.95] mb-6"
            style={{ fontSize: "clamp(3.25rem, 11vw, 7rem)" }}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.85,
              delay: 0.12,
              ease: [0.25, 0.1, 0.25, 1],
            }}
          >
            ScrollMates
          </motion.h1>

          {/* Tagline */}
          <motion.p
            className="font-body text-[#855049] text-lg font-light tracking-[0.01em] mb-5"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.26 }}
          >
            Upload your scroll. Meet your match.
          </motion.p>

          {/* Animated divider — draws in from center */}
          <motion.div
            className="h-px bg-gradient-to-r from-transparent via-[#542822]/20 to-transparent mb-5"
            style={{ width: 64 }}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          />

          {/* Description */}
          <motion.p
            className="font-body text-[#9a8a82] text-[0.85rem] font-light max-w-[20rem] leading-relaxed mb-14"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.48 }}
          >
            Share a scrolling session and discover the people who browse just
            like you — revealed on drop day.
          </motion.p>

          {/* CTA with subtle glow */}
          <motion.button
            onClick={onGetStarted}
            className="relative bg-[#542822] text-[#fef2e8] font-body font-medium text-sm tracking-[0.02em]
                       px-10 py-4 rounded-full cursor-pointer
                       hover:bg-[#6b342d] active:bg-[#452018] transition-colors duration-300"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
          >
            {/* Button glow */}
            <span
              className="absolute inset-0 rounded-full pointer-events-none"
              style={{
                boxShadow: "0 8px 30px rgba(84,40,34,0.2)",
              }}
            />
            Get Started
          </motion.button>
        </div>
      </div>

      {/* Subtle scroll indicator at bottom */}
      <motion.div
        className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3 }}
        transition={{ duration: 0.8, delay: 1.2 }}
      >
        <motion.div
          className="w-px h-6 bg-[#542822]"
          animate={{ scaleY: [1, 0.5, 1], opacity: [0.3, 0.15, 0.3] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
      </motion.div>
    </section>
  )
}
