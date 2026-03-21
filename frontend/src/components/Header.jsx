export default function Header({ onReset }) {
  return (
    <header className="fixed top-0 w-full z-50 glass-subtle animate-fade-up" style={{ animationDelay: '0.1s' }}>
      <div className="flex justify-between items-center px-8 py-4 w-full">
        <div />
        <button type="button" className="flex items-center gap-2 cursor-pointer" onClick={onReset}>
          <img src="/capybara-cropped.png" alt="ScrollMates logo" className="w-16 h-16 object-contain" />
          <h1 className="font-headline font-bold tracking-tight uppercase text-sm text-brand">ScrollMates</h1>
        </button>
        <div />
      </div>
    </header>
  )
}
