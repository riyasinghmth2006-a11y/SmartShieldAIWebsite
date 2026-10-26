import { useEffect, useState } from 'react'
import { I, Ic, Shield3D } from '../components/Visuals'

type State = 'empty' | 'analyzing' | 'results' | 'error'
type Mode = 'message' | 'url'
const MAX = 2000

const CHECKS = [
  { id: 'urgency', label: 'Suspicious urgency', re: /\b(urgent|immediately|act now|within \d+ (hours?|minutes?)|final notice|suspended|expires?|last chance)\b/i, note: 'Pressure to act quickly is a common tactic to stop you from thinking.' },
  { id: 'sensitive', label: 'Requests for sensitive information', re: /\b(password|otp|pin|ssn|social security|card number|cvv|verify your (account|identity)|login details)\b/i, note: 'Legitimate organizations rarely ask for credentials by message.' },
  { id: 'payment', label: 'Unusual payment requests', re: /\b(gift ?cards?|wire transfer|crypto|bitcoin|western union|processing fee|pay (a )?fee)\b/i, note: 'Gift cards, crypto, and wire transfers are hard to reverse.' },
  { id: 'url', label: 'Suspicious URL characteristics', re: /(https?:\/\/\d{1,3}(\.\d{1,3}){3}|bit\.ly|tinyurl|t\.co\/|https?:\/\/[^\s]*@|xn--|\.(zip|top|xyz|click)\b|https?:\/\/[^\s/]*-[^\s/]*-[^\s/]*\.)/i, note: 'Shortened, mismatched, or unusual link patterns can hide the real destination.' },
]

function analyze(text: string, mode: Mode) {
  const hits = CHECKS.filter((c) => c.re.test(text) || (mode === 'url' && c.id === 'url' && !/^https:\/\//i.test(text.trim())))
  const level = hits.length === 0 ? 'None found' : hits.length === 1 ? 'Some signals' : 'Multiple signals'
  return { hits, level }
}

export default function Scam() {
  const [mode, setMode] = useState<Mode>('message')
  const [text, setText] = useState('')
  const [state, setState] = useState<State>('empty')
  const [result, setResult] = useState(analyze('', 'message'))

  useEffect(() => {
    if (state !== 'analyzing') return
    const t = setTimeout(() => setState('results'), 1800)
    return () => clearTimeout(t)
  }, [state])

  const run = () => {
    if (text.trim().length < 8) return setState('error')
    setResult(analyze(text, mode))
    setState('analyzing')
  }

  const demo = (s: State) => {
    if (s === 'results' && !text.trim()) {
      const sample = 'URGENT: Your account will be suspended within 24 hours. Verify your password at http://secure-login-bank-update.xyz or pay a processing fee in gift cards.'
      setMode('message')
      setText(sample)
      setResult(analyze(sample, 'message'))
    }
    if (s === 'empty') setText('')
    if (s === 'analyzing' && !text.trim()) setText('Your parcel is held. Confirm details: http://bit.ly/3xYz')
    if (s === 'analyzing') setResult(analyze(text || 'bit.ly', mode))
    setState(s)
  }

  const tone = result.hits.length === 0 ? 'cyan' : result.hits.length === 1 ? 'amber' : 'rose'
  const toneCls = { cyan: 'text-cyan border-cyan/40 bg-cyan/10', amber: 'text-amber-300 border-amber-300/40 bg-amber-300/10', rose: 'text-rose-400 border-rose-400/40 bg-rose-400/10' }[tone]
  const meter = Math.min(result.hits.length, 3) / 3

  return (
    <div className="fadeup">
      <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">Scam Detector</h1>
      <p className="mt-3 text-lg text-mute">Analyze suspicious messages and URLs for common warning signs.</p>

      <div className="mt-6 flex flex-wrap items-center gap-2 text-xs text-mute">
        <span className="font-bold tracking-widest">PREVIEW STATE</span>
        {(['empty', 'analyzing', 'results', 'error'] as State[]).map((s) => (
          <button key={s} onClick={() => demo(s)} className={`rounded-full border px-3 py-1 font-semibold capitalize ${state === s ? 'border-cyan bg-cyan/10 text-cyan' : 'border-line hover:text-ink'}`}>{s === 'error' ? 'Validation error' : s}</button>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
        <section className="glass rounded-3xl p-5 md:p-7">
          <div role="tablist" className="inline-flex rounded-xl border border-line bg-bg/70 p-1">
            {(['message', 'url'] as Mode[]).map((m) => (
              <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)} className={`rounded-lg px-5 py-2 text-sm font-bold transition-all ${mode === m ? 'bg-blue text-white shadow-[0_6px_18px_-6px_#1685ff]' : 'text-mute hover:text-ink'}`}>
                {m === 'message' ? 'Message' : 'URL'}
              </button>
            ))}
          </div>
          <label htmlFor="scam-in" className="mt-6 block text-sm font-bold">{mode === 'message' ? 'Suspicious message' : 'Link to inspect'}</label>
          <textarea
            id="scam-in"
            value={text}
            maxLength={MAX}
            onChange={(e) => { setText(e.target.value); if (state === 'error') setState('empty') }}
            placeholder={mode === 'message' ? 'Paste the text of an email, SMS, or chat message you are unsure about…' : 'Paste a link, e.g. http://example-login.verify-now.xyz'}
            className={`mt-2 w-full resize-none rounded-2xl border bg-bg/70 p-4 text-base leading-relaxed text-ink outline-none transition-colors placeholder:text-mute/60 focus:border-cyan ${mode === 'url' ? 'h-24' : 'h-48'} ${state === 'error' ? 'border-rose-400' : 'border-line'}`}
          />
          <div className="mt-2 flex items-center justify-between text-sm">
            {state === 'error' ? (
              <p role="alert" className="flex items-center gap-2 font-semibold text-rose-400"><Ic d={I.warn} size={16} /> Please enter at least a few words or a full link to analyze.</p>
            ) : <span />}
            <span className="text-mute">{text.length} / {MAX}</span>
          </div>
          <button onClick={run} disabled={state === 'analyzing'} className="btn-primary mt-5 w-full rounded-xl px-8 py-4 font-bold text-white disabled:opacity-60 sm:w-auto">
            {state === 'analyzing' ? 'Analyzing…' : 'Analyze'}
          </button>
        </section>

        <aside className="glass rounded-3xl p-6">
          <div className="-mt-2 flex justify-center"><Shield3D size={150} /></div>
          <h3 className="mt-2 text-xl font-extrabold">Stay Safe Online</h3>
          <p className="mt-1 text-sm text-mute">Watch for these warning indicators:</p>
          <ul className="mt-4 space-y-3">
            {CHECKS.map((c) => (
              <li key={c.id} className="flex items-start gap-3 text-sm font-semibold">
                <span className="mt-0.5 text-cyan"><Ic d={I.warn} size={18} /></span> {c.label}
              </li>
            ))}
          </ul>
        </aside>
      </div>

      {state === 'analyzing' && (
        <section className="glass fadeup relative mt-6 overflow-hidden rounded-3xl p-8" aria-live="polite">
          <div className="flex items-center gap-5">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-line border-t-cyan" />
            <div>
              <h3 className="text-lg font-bold">Analyzing for warning signs…</h3>
              <p className="text-sm text-mute">Checking urgency, requests, payments, and link patterns.</p>
            </div>
          </div>
          <div className="mt-6 h-1.5 overflow-hidden rounded-full bg-line"><div className="h-full w-full animate-pulse rounded-full bg-gradient-to-r from-blue to-cyan" /></div>
        </section>
      )}

      {state === 'results' && (
        <section className="fadeup mt-6 grid gap-6 lg:grid-cols-[360px_1fr]">
          <div className="glass rounded-3xl p-7">
            <p className="text-xs font-bold tracking-[0.18em] text-mute">WARNING SIGNALS</p>
            <div className={`mt-3 inline-block rounded-full border px-4 py-1.5 text-sm font-extrabold ${toneCls}`}>{result.level}</div>
            <div className="mt-6 flex gap-1.5" role="img" aria-label={`${result.hits.length} of 4 warning signals found`}>
              {[0, 1, 2, 3].map((i) => (
                <span key={i} className={`h-2.5 flex-1 rounded-full ${i < result.hits.length ? (tone === 'rose' ? 'bg-rose-400' : tone === 'amber' ? 'bg-amber-300' : 'bg-cyan') : 'bg-line'}`} />
              ))}
            </div>
            <p className="mt-2 text-sm text-mute">{result.hits.length} of 4 indicator types found{meter > 0 ? '' : ''}</p>
            <p className="mt-6 rounded-xl border border-line bg-bg/60 p-4 text-sm leading-relaxed text-mute">This is a heuristic check, not proof. A low result does not mean a message is safe, and a high result does not prove fraud.</p>
          </div>
          <div className="glass rounded-3xl p-7">
            <h3 className="text-lg font-extrabold">Detected signals</h3>
            {result.hits.length === 0 ? (
              <p className="mt-3 text-mute">No common warning patterns were detected. Stay cautious with anything unexpected.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {result.hits.map((h) => (
                  <li key={h.id} className="rounded-xl border border-line bg-bg/50 p-4">
                    <p className="font-bold">{h.label}</p>
                    <p className="mt-1 text-sm text-mute">{h.note}</p>
                  </li>
                ))}
              </ul>
            )}
            <h3 className="mt-7 text-lg font-extrabold">What this means</h3>
            <p className="mt-2 leading-relaxed text-mute">
              {result.hits.length === 0 ? 'Our simple checks did not match known patterns, but scams evolve and can look perfectly normal.' : 'The content contains characteristics often seen in scam attempts. That makes it worth extra scrutiny before you respond or click.'}
            </p>
            <h3 className="mt-7 text-lg font-extrabold">Recommended next steps</h3>
            <ol className="mt-3 space-y-2 text-mute">
              {['Do not click links or share personal details yet.', 'Contact the organization using a number or site you already trust.', 'Report or delete the message if it still seems suspicious.'].map((s, i) => (
                <li key={s} className="flex gap-3"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue/20 text-xs font-bold text-cyan">{i + 1}</span>{s}</li>
              ))}
            </ol>
          </div>
        </section>
      )}
    </div>
  )
}
