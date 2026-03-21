export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 w-full z-50 glass-subtle">
      <div className="flex justify-around items-center px-12 pb-8 pt-4">
        <a className="flex flex-col items-center justify-center text-secondary p-3 transition-colors hover:text-brand" href="#">
          <span className="material-symbols-outlined">home</span>
        </a>
        <a className="flex flex-col items-center justify-center rounded-full p-3 transition-all duration-300 bg-brand/10 text-brand" href="#">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add_circle</span>
        </a>
        <a className="flex flex-col items-center justify-center text-secondary p-3 transition-colors hover:text-brand" href="#">
          <span className="material-symbols-outlined">person</span>
        </a>
      </div>
    </nav>
  )
}
