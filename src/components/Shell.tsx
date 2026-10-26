import { useState, type ReactNode } from 'react'
import { I, Ic, Logo, Particles } from './Visuals'

export type Page = 'home' | 'scam' | 'news' | 'deepfake' | 'how' | 'about'

export const NAV: { id: Page; label: string; icon: ReactNode }[] = [
  { id: 'home', label: 'Home', icon: I.home },
  { id: 'scam', label: 'Scam Detector', icon: I.shield },
  { id: 'news', label: 'Fake News Detector', icon: I.news },
  { id: 'deepfake', label: 'Deepfake Detector', icon: I.media },
  { id: 'how', label: 'How It Works', icon: I.flow },
  { id: 'about', label: 'About', icon: I.info },
]

function Brand({ go }: { go: (p: Page) => void }) {
  return (
    <button onClick={() => go('home')} className="flex items-center gap-2.5 text-left">
      <Logo />
      <span className="text-lg font-extrabold tracking-tight">
        SmartShield <span className="text-cyan">AI</span>
      </span>
    </button>
  )
}

function MobileMenu({ page, go }: { page: Page; go: (p: Page) => void }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button aria-label="Toggle menu" onClick={() => setOpen(!open)} className="grid h-11 w-11 place-items-center rounded-xl border border-line text-ink lg:hidden">
        <Ic d={open ? I.close : I.menu} />
      </button>
      {open && (
        <div className="glass fadeup absolute inset-x-4 top-[72px] z-50 rounded-2xl p-2 lg:hidden">
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => {
                go(n.id)
                setOpen(false)
              }}
              className={`flex w-full items-center gap-3 rounded-xl px-4 py-3.5 text-left font-semibold ${page === n.id ? 'bg-blue/20 text-cyan' : 'text-mute'}`}
            >
              <Ic d={n.icon} size={20} /> {n.label}
            </button>
          ))}
          <button onClick={() => { go('scam'); setOpen(false) }} className="btn-primary mt-2 w-full rounded-xl px-4 py-3.5 font-bold text-white">
            Start Scanning
          </button>
        </div>
      )}
    </>
  )
}

export function Background() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-0 overflow-hidden">
      <div className="absolute -right-40 -top-40 h-[640px] w-[640px] rounded-full bg-blue/20 blur-[140px]" />
      <div className="absolute -left-40 top-1/2 h-[480px] w-[480px] rounded-full bg-violet/10 blur-[140px]" />
      <div className="grid-bg absolute inset-0" />
      <Particles count={14} />
    </div>
  )
}

export function TopNav({ page, go }: { page: Page; go: (p: Page) => void }) {
  return (
    <header className="relative z-40 mx-auto flex h-[84px] max-w-[1280px] items-center justify-between px-5 md:px-8">
      <Brand go={go} />
      <nav className="hidden items-center gap-1 lg:flex">
        {NAV.map((n) => (
          <button key={n.id} onClick={() => go(n.id)} className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors hover:text-ink ${page === n.id ? 'text-cyan' : 'text-mute'}`}>
            {n.label}
          </button>
        ))}
      </nav>
      <div className="flex items-center gap-3">
        <button onClick={() => go('scam')} className="btn-primary hidden rounded-xl px-5 py-2.5 text-sm font-bold text-white sm:block">
          Start Scanning
        </button>
        <MobileMenu page={page} go={go} />
      </div>
    </header>
  )
}

export function AppFrame({ page, go, children }: { page: Page; go: (p: Page) => void; children: ReactNode }) {
  return (
    <div className="relative z-10 flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-[272px] shrink-0 flex-col border-r border-line/70 bg-bg2/70 p-6 backdrop-blur lg:flex">
        <Brand go={go} />
        <nav className="mt-10 flex flex-col gap-1.5">
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => go(n.id)}
              className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm font-semibold transition-all ${
                page === n.id ? 'border-cyan/40 bg-blue/15 text-ink shadow-[inset_3px_0_0_#22d3ee]' : 'border-transparent text-mute hover:bg-white/5 hover:text-ink'
              }`}
            >
              <span className={page === n.id ? 'text-cyan' : ''}><Ic d={n.icon} size={20} /></span>
              {n.label}
            </button>
          ))}
        </nav>
        <p className="mt-auto text-xs leading-relaxed text-mute">Student project. Results are not a guarantee of safety or factual accuracy.</p>
      </aside>
      <div className="relative min-w-0 flex-1">
        <div className="relative z-40 flex h-[72px] items-center justify-between px-5 lg:hidden">
          <Brand go={go} />
          <MobileMenu page={page} go={go} />
        </div>
        <main className="mx-auto max-w-[1100px] px-5 pb-20 pt-4 md:px-10 lg:pt-12">{children}</main>
      </div>
    </div>
  )
}

export function Footer({ go }: { go: (p: Page) => void }) {
  return (
    <footer className="relative z-10 border-t border-line/70 bg-bg2/60">
      <div className="mx-auto grid max-w-[1280px] gap-10 px-5 py-14 md:grid-cols-[1.3fr_1fr_1fr] md:px-8">
        <div>
          <Brand go={go} />
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-mute">Your digital safety companion for examining suspicious messages, links, and news text.</p>
        </div>
        <div>
          <h4 className="text-sm font-bold">Explore</h4>
          <ul className="mt-4 space-y-2.5">
            {NAV.map((n) => (
              <li key={n.id}>
                <button onClick={() => go(n.id)} className="text-sm text-mute hover:text-cyan">{n.label}</button>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-bold">Technology</h4>
          <p className="mt-4 text-sm leading-relaxed text-mute">Python, Streamlit, machine learning, and natural language processing, combined with rule-based heuristic checks. Deepfake analysis is a prototype interface pending a detection model.</p>
          <h4 className="mt-6 text-sm font-bold">Limitations</h4>
          <p className="mt-2 text-sm leading-relaxed text-mute">Heuristics miss novel scams. The news model may be unavailable. Deepfake detection is a prototype UI until a model is configured.</p>
        </div>
      </div>
      <div className="border-t border-line/50 px-5 py-5 text-center text-xs text-mute">Student project. Results are not a guarantee of safety or factual accuracy.</div>
    </footer>
  )
}
