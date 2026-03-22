export default function Header({ onReset, onSignOut }) {
  return (
    <header className="fixed inset-x-0 top-0 z-50 w-full overflow-x-clip box-border glass-subtle animate-fade-up" style={{ animationDelay: '0.1s' }}>
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4 lg:px-8">
        <button
          type="button"
          className="flex min-w-0 items-center gap-2 text-left cursor-pointer sm:gap-3"
          onClick={onReset}
        >
          <img src="/capybara-cropped.png" alt="ScrollMates logo" className="h-12 w-12 shrink-0 object-contain sm:h-14 sm:w-14" />
          <div className="min-w-0">
            <span className="font-headline text-xs font-bold uppercase tracking-[0.16em] text-brand sm:hidden">
              SM
            </span>
            <span className="hidden truncate font-headline text-sm font-bold tracking-tight uppercase text-brand sm:block">
              ScrollMates
            </span>
          </div>
        </button>
        <div className="flex min-w-0 shrink-0 justify-end">
          {onSignOut ? (
            <button
              type="button"
              className="rounded-lg px-2 py-1.5 font-label text-[0.65rem] uppercase tracking-[0.15em] text-brand/70 transition-colors hover:bg-brand/5 hover:text-brand cursor-pointer sm:px-3 sm:text-xs"
              onClick={onSignOut}
            >
              Sign Out
            </button>
          ) : null}
        </div>
      </div>
    </header>
  )
}
