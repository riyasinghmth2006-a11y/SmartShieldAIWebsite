import { I, Ic, Icon3D, MagnifierShield, MediaFrame3D, NewsScan, Shield3D } from '../components/Visuals'
import type { Page } from '../components/Shell'

const steps = [
  { n: '01', t: 'Enter Content', d: 'Paste a message, URL, or news text.', i: I.input, tone: 'blue' as const },
  { n: '02', t: 'Analyze Signals', d: 'Heuristic checks or a trained model examine it.', i: I.cpu, tone: 'cyan' as const },
  { n: '03', t: 'Review Findings', d: 'Read the signals found and suggested next steps.', i: I.list, tone: 'violet' as const },
]

export default function Home({ go }: { go: (p: Page) => void }) {
  return (
    <div className="relative z-10">
      <section className="mx-auto grid max-w-[1280px] items-center gap-6 px-5 pb-16 pt-6 md:px-8 lg:grid-cols-[1.05fr_1fr] lg:pt-10">
        <div className="fadeup">
          <p className="inline-flex items-center gap-2 rounded-full border border-line bg-card/60 px-4 py-1.5 text-xs font-bold tracking-[0.18em] text-cyan">
            <span className="h-1.5 w-1.5 rounded-full bg-cyan shadow-[0_0_8px_#22d3ee]" /> AI-POWERED DIGITAL SECURITY
          </p>
          <h1 className="mt-6 text-[44px] font-extrabold leading-[1.02] tracking-[-0.03em] sm:text-6xl lg:text-[84px]">
            Stay Ahead of <span className="text-grad">Digital Threats.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-mute">
            Analyze suspicious messages, investigate risky links, and make smarter decisions online with AI-assisted digital safety tools.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <button onClick={() => go('scam')} className="btn-primary rounded-xl px-7 py-4 text-base font-bold text-white">Start Scanning</button>
            <button
              onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
              className="rounded-xl border border-line bg-white/[0.03] px-7 py-4 text-base font-bold transition-colors hover:border-cyan/60 hover:bg-white/[0.06]"
            >
              Explore Features
            </button>
          </div>
        </div>
        <div className="relative mx-auto grid w-full place-items-center py-6">
          <div className="hidden lg:block"><Shield3D size={560} /></div>
          <div className="hidden sm:block lg:hidden"><Shield3D size={440} /></div>
          <div className="sm:hidden"><Shield3D size={280} /></div>
        </div>
      </section>

      <section id="features" className="mx-auto grid max-w-[1280px] gap-6 px-5 py-10 md:px-8 md:grid-cols-2 lg:grid-cols-3">
        {[
          { t: 'Scam Detection', d: 'Analyze suspicious messages and URLs for common warning signs.', cta: 'Analyze a Message', to: 'scam' as Page, v: <MagnifierShield />, c: 'from-blue/25' },
          { t: 'Fake News Detection', d: 'Examine news text using machine-learning analysis when a trained model is available.', cta: 'Check News', to: 'news' as Page, v: <NewsScan />, c: 'from-violet/25' },
          { t: 'Deepfake Detection', d: 'Analyze images and videos for potential signs of AI-generated or digitally manipulated content.', cta: 'Analyze Media', to: 'deepfake' as Page, v: <MediaFrame3D />, c: 'from-cyan/20' },
        ].map((f) => (
          <article key={f.t} className={`glass glass-hover group relative overflow-hidden rounded-3xl p-7 md:p-8 ${f.to === 'deepfake' ? 'md:col-span-2 lg:col-span-1' : ''}`}>
            <div className={`absolute inset-0 bg-gradient-to-br ${f.c} to-transparent opacity-60`} />
            <div className="relative flex h-full flex-col gap-6">
              <div className="mx-auto h-36 w-52 shrink-0 transition-transform duration-300 group-hover:scale-110">{f.v}</div>
              <div className="flex flex-1 flex-col">
                <h3 className="text-2xl font-extrabold tracking-tight">{f.t}</h3>
                <p className="mt-3 leading-relaxed text-mute">{f.d}</p>
                <button onClick={() => go(f.to)} className="mt-auto inline-flex items-center gap-2 pt-6 font-bold text-cyan transition-all group-hover:gap-3">
                  {f.cta} <span aria-hidden>→</span>
                </button>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="mx-auto max-w-[1280px] px-5 py-20 md:px-8">
        <div className="max-w-xl">
          <p className="text-xs font-bold tracking-[0.18em] text-cyan">HOW IT WORKS</p>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight md:text-4xl">Three steps from doubt to a clearer decision.</h2>
        </div>
        <div className="relative mt-10 grid gap-5 md:grid-cols-3">
          <div className="absolute left-[16%] right-[16%] top-[58px] hidden h-px bg-gradient-to-r from-blue via-cyan to-violet opacity-60 md:block" />
          {steps.map((s) => (
            <div key={s.n} className="glass glass-hover relative rounded-2xl p-6">
              <div className="flex items-center justify-between">
                <Icon3D tone={s.tone}><Ic d={s.i} /></Icon3D>
                <span className="text-4xl font-extrabold text-line">{s.n}</span>
              </div>
              <h3 className="mt-5 text-lg font-bold">{s.t}</h3>
              <p className="mt-2 text-sm leading-relaxed text-mute">{s.d}</p>
            </div>
          ))}
        </div>
        <button onClick={() => go('how')} className="mt-8 font-bold text-cyan hover:underline">See the full workflow →</button>
      </section>
    </div>
  )
}
