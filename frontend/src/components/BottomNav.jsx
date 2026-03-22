export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 z-50 w-full overflow-x-clip glass-subtle">
      <div className="mx-auto flex w-full max-w-md items-center justify-around px-4 pb-8 pt-4 sm:px-6">
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
