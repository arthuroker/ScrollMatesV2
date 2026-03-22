import { useState } from 'react'

export default function SignInScreen({ onSignIn }) {
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const isSignIn = mode === 'signin'

  const handleSubmit = (e) => {
    e.preventDefault()
    onSignIn({ email, password })
  }

  return (
    <main className="box-border min-h-screen w-full max-w-full overflow-x-clip flex flex-col items-center px-8 pt-28">
      <div className="w-full max-w-xs">
        <div className="flex flex-col items-center mb-8 animate-fade-up" style={{ animationDelay: '0.15s' }}>
          <img src="/capybara-cropped.png" alt="ScrollMates logo" className="w-20 h-20 object-contain mb-3" />
          <h1 className="font-headline font-bold tracking-tight uppercase text-sm text-brand">ScrollMates</h1>
        </div>

        <div className="flex w-full rounded-xl glass mb-6 p-1 animate-fade-up" style={{ animationDelay: '0.2s' }}>
          <button
            type="button"
            onClick={() => setMode('signin')}
            className={`flex-1 py-2.5 rounded-lg font-headline font-bold text-sm text-center transition-all duration-300 cursor-pointer ${
              isSignIn
                ? 'bg-brand/85 text-on-primary shadow-md shadow-brand/15'
                : 'text-brand/40 hover:text-brand/60'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setMode('signup')}
            className={`flex-1 py-2.5 rounded-lg font-headline font-bold text-sm text-center transition-all duration-300 cursor-pointer ${
              !isSignIn
                ? 'bg-brand/85 text-on-primary shadow-md shadow-brand/15'
                : 'text-brand/40 hover:text-brand/60'
            }`}
          >
            Sign Up
          </button>
        </div>

        <h2 className="font-headline text-2xl font-extrabold text-brand mb-5 animate-fade-up" style={{ animationDelay: '0.25s' }}>
          {isSignIn ? 'Welcome back' : 'Create account'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="animate-fade-up" style={{ animationDelay: '0.3s' }}>
            <label className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/50 mb-1.5 block px-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full glass rounded-xl px-4 py-3 text-sm font-body text-brand placeholder-brand/30 outline-none focus:ring-2 focus:ring-brand/20 transition-shadow"
              placeholder="you@example.com"
            />
          </div>

          <div className="animate-fade-up" style={{ animationDelay: '0.4s' }}>
            <label className="font-label text-[10px] uppercase tracking-[0.2em] text-brand/50 mb-1.5 block px-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full glass rounded-xl px-4 py-3 text-sm font-body text-brand placeholder-brand/30 outline-none focus:ring-2 focus:ring-brand/20 transition-shadow"
              placeholder="••••••••"
            />
          </div>

          <div className="animate-fade-up pt-2" style={{ animationDelay: '0.5s' }}>
            <button
              type="submit"
              className="w-full py-3.5 px-6 rounded-lg text-on-primary font-headline font-bold text-sm text-center transition-all duration-300 active:scale-[0.98] bg-brand/85 backdrop-blur-md shadow-lg shadow-brand/15 border border-brand/20"
            >
              {isSignIn ? 'Sign In' : 'Create Account'}
            </button>
          </div>
        </form>
      </div>
    </main>
  )
}
