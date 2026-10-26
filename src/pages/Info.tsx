import { I, Ic, Icon3D, Shield3D } from '../components/Visuals'
import type { Page } from '../components/Shell'

const flow = [
  { t: 'Input', d: 'Submit a message, URL, or news text.', i: I.input, tone: 'blue' as const },
  { t: 'Validation', d: 'Check and prepare the input.', i: I.check, tone: 'cyan' as const },
  { t: 'Analysis', d: 'Use available heuristic checks or a trained ML model.', i: I.cpu, tone: 'violet' as const },
  { t: 'Results', d: 'Display findings and recommendations.', i: I.list, tone: 'blue' as const },
  { t: 'Verification', d: 'Independently verify important information.', i: I.verify, tone: 'cyan' as const },
]
const tech = [
  ['Python', 'Core language for the analysis logic.'],
  ['Streamlit', 'Lightweight framework for the app interface.'],
  ['Machine Learning', 'A trained text classifier for news, when available.'],
  ['Natural Language Processing', 'Text preparation and feature extraction.'],
]
const limits = [
  'Heuristic checks only catch known patterns; new scams can slip through.',
  'The news model can be wrong and may be unavailable.',
  'Results are guidance, never proof of safety or factual accuracy.',
  'Deepfake analysis is a prototype interface: no detection model is confirmed yet, and file support depends on the eventual backend.',
]

function Head({ eyebrow, title, sub }: { eyebrow: string; title: string; sub?: string }) {
  return (
    <div className="max-w-2xl">
      <p className="text-xs font-bold tracking-[0.18em] text-cyan">{eyebrow}</p>
      <h1 className="mt-3 text-4xl font-extrabold tracking-tight md:text-5xl">{title}</h1>
      {sub && <p className="mt-4 text-lg leading-relaxed text-mute">{sub}</p>}
    </div>
  )
}

function Limits() {
  return (
    <section className="glass rounded-3xl border-amber-300/20 p-7">
      <h2 className="flex items-center gap-3 text-xl font-extrabold"><span className="text-amber-300"><Ic d={I.warn} /></span> Limitations</h2>
      <ul className="mt-4 grid gap-3 text-mute md:grid-cols-2">
        {limits.map((l) => <li key={l} className="flex gap-3"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-300" />{l}</li>)}
      </ul>
    </section>
  )
}

export function How() {
  return (
    <div className="fadeup space-y-14">
      <Head eyebrow="HOW IT WORKS" title="From input to informed decision." sub="SmartShield AI follows a simple, transparent workflow so you always know what was checked." />
      <ol className="relative space-y-5 pl-0">
        <div className="absolute bottom-10 left-[27px] top-10 w-px bg-gradient-to-b from-blue via-cyan to-violet shadow-[0_0_12px_#1685ff]" />
        {flow.map((s, i) => (
          <li key={s.t} className="glass glass-hover relative ml-0 flex items-center gap-5 rounded-2xl p-5 md:p-6">
            <Icon3D tone={s.tone}><Ic d={s.i} /></Icon3D>
            <div>
              <p className="text-xs font-bold tracking-widest text-cyan">STEP {i + 1}</p>
              <h3 className="text-lg font-bold">{s.t}</h3>
              <p className="text-mute">{s.d}</p>
            </div>
          </li>
        ))}
      </ol>
      <section>
        <h2 className="text-2xl font-extrabold">Technology</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {tech.map(([t, d]) => (
            <div key={t} className="glass glass-hover rounded-2xl p-5">
              <h3 className="font-bold text-cyan">{t}</h3>
              <p className="mt-2 text-sm leading-relaxed text-mute">{d}</p>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2 className="text-2xl font-extrabold">Three detection capabilities</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {[
            ['Scam Detector', 'Working', 'Rule-based heuristic checks on messages and URLs.', 'text-cyan bg-cyan/15'],
            ['Fake News Detector', 'Model dependent', 'Works only when a trained model is available.', 'text-amber-300 bg-amber-300/15'],
            ['Deepfake Detector', 'Planned · prototype UI', 'Interface designed; detection backend not yet confirmed.', 'text-violet bg-violet/15'],
          ].map(([t, tag, d, c]) => (
            <div key={t} className="glass glass-hover rounded-2xl p-5">
              <span className={`rounded-full px-3 py-1 text-xs font-extrabold ${c}`}>{tag}</span>
              <h3 className="mt-3 font-bold">{t}</h3>
              <p className="mt-2 text-sm leading-relaxed text-mute">{d}</p>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2 className="text-2xl font-extrabold">Media workflow <span className="ml-2 align-middle rounded-full bg-violet/15 px-3 py-1 text-xs font-extrabold text-violet">PLANNED</span></h2>
        <ol className="mt-5 grid gap-3 md:grid-cols-5">
          {['Upload an image or video.', 'Validate the file.', 'Analyze with an available detection model.', 'Display supported findings and limitations.', 'Verify independently when necessary.'].map((t, i) => (
            <li key={t} className="glass rounded-2xl p-4 text-sm text-mute"><span className="mb-2 block text-xs font-bold tracking-widest text-cyan">0{i + 1}</span>{t}</li>
          ))}
        </ol>
      </section>
      <Limits />
    </div>
  )
}

export function About({ go }: { go: (p: Page) => void }) {
  const now = ['Heuristic scam checks for messages and URLs', 'ML-assisted news text analysis, when a trained model is available', 'Plain-language explanations and next steps']
  const road = ['Improved ML models', 'Deepfake detection model integration (interface prototyped)', 'Persistent scan history', 'Optional browser integration']
  return (
    <div className="fadeup space-y-12">
      <div className="grid items-center gap-6 md:grid-cols-[1.3fr_1fr]">
        <Head eyebrow="ABOUT SMARTSHIELD AI" title="Your digital safety companion." sub="Mission: help people pause, examine, and verify before they trust, click, or share." />
        <div className="hidden justify-center md:flex"><Shield3D size={260} /></div>
      </div>
      <section className="glass rounded-3xl p-7">
        <h2 className="text-xl font-extrabold">Project overview</h2>
        <p className="mt-3 max-w-3xl leading-relaxed text-mute">SmartShield AI is a student project exploring how heuristics and machine learning can support everyday online safety. It offers guidance, not guarantees, and is built to be honest about what it can and cannot do.</p>
        <h3 className="mt-6 font-bold">Technology stack</h3>
        <div className="mt-3 flex flex-wrap gap-2">{tech.map(([t]) => <span key={t} className="rounded-full border border-line bg-bg/60 px-4 py-1.5 text-sm font-semibold text-mute">{t}</span>)}</div>
      </section>
      <div className="grid gap-6 md:grid-cols-2">
        <section className="glass rounded-3xl border-cyan/30 p-7">
          <p className="inline-block rounded-full bg-cyan/15 px-3 py-1 text-xs font-extrabold tracking-widest text-cyan">AVAILABLE NOW</p>
          <h2 className="mt-3 text-xl font-extrabold">Current capabilities</h2>
          <ul className="mt-4 space-y-3 text-mute">{now.map((n) => <li key={n} className="flex gap-3"><span className="text-cyan"><Ic d={I.check} size={18} /></span>{n}</li>)}</ul>
        </section>
        <section className="glass rounded-3xl border-dashed border-violet/40 p-7">
          <p className="inline-block rounded-full bg-violet/15 px-3 py-1 text-xs font-extrabold tracking-widest text-violet">PLANNED, NOT BUILT</p>
          <h2 className="mt-3 text-xl font-extrabold">Future roadmap</h2>
          <ul className="mt-4 space-y-3 text-mute">{road.map((n) => <li key={n} className="flex gap-3"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet" />{n}</li>)}</ul>
        </section>
      </div>
      <Limits />
      <button onClick={() => go('scam')} className="btn-primary rounded-xl px-7 py-4 font-bold text-white">Start Scanning</button>
    </div>
  )
}
