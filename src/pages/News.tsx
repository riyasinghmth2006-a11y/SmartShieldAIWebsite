import { useEffect, useRef, useState } from 'react'
import { I, Ic } from '../components/Visuals'

type State = 'empty' | 'analyzing' | 'results' | 'error' | 'unavailable'
const MAX = 5000
const EXAMPLE = 'Scientists announce miracle fruit that cures every disease overnight, doctors stunned, officials say they are hiding it from the public.'

export default function News() {
  const [text, setText] = useState('')
  const [state, setState] = useState<State>('empty')
  const [modelResult, setModelResult] = useState<{ label: string; confidence?: number | null; explanation?: string } | null>(null)
  const [unavailableNotice, setUnavailableNotice] = useState({
    title: 'Model currently unavailable',
    desc: 'No trained model is loaded right now, so we cannot produce a prediction. We would rather show nothing than a guess. Cross-check the claim with trusted outlets or a fact-checking organization in the meantime.',
  })
  const isLive = useRef(false)

  useEffect(() => {
    let mounted = true
    fetch('/api/health')
      .then((res) => {
        if (!res.ok) throw new Error('Health check non-200')
        return res.json()
      })
      .then((data) => {
        if (!mounted) return
        if (data.models_configured && !data.models_configured.fake_news_model) {
          setUnavailableNotice({
            title: 'Model currently unavailable',
            desc: 'No trained model is loaded right now, so we cannot produce a prediction. We would rather show nothing than a guess. Cross-check the claim with trusted outlets or a fact-checking organization in the meantime.',
          })
          setState((prev) => (prev === 'empty' ? 'unavailable' : prev))
        }
      })
      .catch(() => {
        if (!mounted) return
        setUnavailableNotice({
          title: 'Backend connection failure',
          desc: 'Could not connect to the backend at /api/health. Please ensure the Python FastAPI server is running on port 8001.',
        })
        setState((prev) => (prev === 'empty' ? 'unavailable' : prev))
      })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (state !== 'analyzing' || isLive.current) return
    const t = setTimeout(() => setState('unavailable'), 1800)
    return () => clearTimeout(t)
  }, [state])

  const run = async () => {
    if (text.trim().length < 20) return setState('error')
    isLive.current = true
    setState('analyzing')
    try {
      const res = await fetch('/api/fake-news/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() }),
      })
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || 'Request failed')
      }
      const data = await res.json()
      if (data.status === 'completed' && data.label) {
        setModelResult(data)
        setState('results')
      } else {
        setModelResult(null)
        setUnavailableNotice({
          title: 'Model currently unavailable',
          desc: data.explanation || 'No trained model is loaded right now, so we cannot produce a prediction. We would rather show nothing than a guess. Cross-check the claim with trusted outlets or a fact-checking organization in the meantime.',
        })
        setState('unavailable')
      }
    } catch {
      setModelResult(null)
      setUnavailableNotice({
        title: 'Backend connection failure',
        desc: 'Could not connect to the backend at /api/fake-news/analyze. Please ensure the Python FastAPI server is running on port 8001.',
      })
      setState('unavailable')
    } finally {
      isLive.current = false
    }
  }
  const demo = (s: State) => {
    isLive.current = false
    setModelResult(null)
    setUnavailableNotice({
      title: 'Model currently unavailable',
      desc: 'No trained model is loaded right now, so we cannot produce a prediction. We would rather show nothing than a guess. Cross-check the claim with trusted outlets or a fact-checking organization in the meantime.',
    })
    if (s === 'empty') setText('')
    if (s === 'error') setText('')
    setState(s)
  }

  return (
    <div className="fadeup">
      <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">Fake News Detector</h1>
      <p className="mt-3 text-lg text-mute">Examine news content using machine-learning analysis.</p>

      <section className="glass mt-8 rounded-3xl p-5 md:p-7">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label htmlFor="news-in" className="text-sm font-bold">News headline or article text</label>
          <button onClick={() => { setText(EXAMPLE); setState('empty') }} className="text-sm font-bold text-cyan hover:underline">Try an example</button>
        </div>
        <textarea
          id="news-in"
          value={text}
          maxLength={MAX}
          onChange={(e) => { setText(e.target.value); if (state === 'error') setState('empty') }}
          placeholder="Paste a headline or the full text of an article. Longer text gives the model more context to work with…"
          className={`mt-2 h-52 w-full resize-none rounded-2xl border bg-bg/70 p-4 leading-relaxed text-ink outline-none transition-colors placeholder:text-mute/60 focus:border-cyan ${state === 'error' ? 'border-rose-400' : 'border-line'}`}
        />
        <div className="mt-2 flex items-center justify-between text-sm">
          {state === 'error' ? (
            <p role="alert" className="flex items-center gap-2 font-semibold text-rose-400"><Ic d={I.warn} size={16} /> Please enter at least a full sentence (20+ characters) to analyze.</p>
          ) : <span />}
          <span className="text-mute">{text.length} / {MAX}</span>
        </div>
        <button onClick={run} disabled={state === 'analyzing'} className="btn-primary mt-5 w-full rounded-xl px-8 py-4 font-bold text-white disabled:opacity-60 sm:w-auto">
          {state === 'analyzing' ? 'Analyzing…' : 'Analyze'}
        </button>
      </section>

      <p className="mt-4 flex gap-3 text-sm text-mute"><span className="text-cyan"><Ic d={I.info} size={18} /></span>Analysis depends on a trained model being available, and results are never proof that a claim is true or false.</p>

      {state === 'analyzing' && (
        <section className="glass fadeup mt-6 flex items-center gap-5 rounded-3xl p-8" aria-live="polite">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-line border-t-violet" />
          <div>
            <h3 className="text-lg font-bold">Running model analysis…</h3>
            <p className="text-sm text-mute">Preparing text and passing it to the classifier.</p>
          </div>
        </section>
      )}

      {state === 'unavailable' && (
        <section className="glass fadeup mt-6 rounded-3xl border-amber-300/30 p-8">
          <div className="flex items-start gap-4">
            <span className="text-amber-300"><Ic d={I.warn} size={28} /></span>
            <div>
              <h3 className="text-xl font-extrabold">{unavailableNotice.title}</h3>
              <p className="mt-2 max-w-2xl leading-relaxed text-mute">{unavailableNotice.desc}</p>
            </div>
          </div>
        </section>
      )}

      {state === 'results' && (
        <section className="fadeup mt-6 space-y-6">
          {!modelResult && (
            <p className="rounded-xl border border-violet/40 bg-violet/10 p-3 text-sm text-violet">Layout template only. No analysis was run and none of this content is a result.</p>
          )}
          <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
            <div className="glass rounded-3xl p-7">
              <p className="text-xs font-bold tracking-[0.18em] text-mute">MODEL PREDICTION</p>
              <p className="mt-3 text-3xl font-extrabold text-ink">{modelResult?.label || '[Label from model]'}</p>
              <p className="mt-3 text-sm leading-relaxed text-mute">
                {modelResult?.confidence !== undefined && modelResult?.confidence !== null
                  ? `Confidence score: ${(modelResult.confidence * 100).toFixed(1)}%`
                  : 'Shown only after a real analysis. A confidence value appears here only if the model actually supports one.'}
              </p>
            </div>
            <div className="glass rounded-3xl p-7">
              <h3 className="text-lg font-extrabold">Explanation</h3>
              <p className="mt-3 text-sm leading-relaxed text-mute">{modelResult?.explanation || 'A plain-language description of what the model examined and what influenced the output will appear here.'}</p>
              <div className="mt-6 rounded-xl border border-cyan/30 bg-cyan/5 p-4">
                <p className="font-bold text-cyan">Verify independently</p>
                <p className="mt-1 text-sm leading-relaxed text-mute">An AI classification is not proof that a claim is true or false. Check original sources, reputable outlets, and fact-checkers before sharing.</p>
              </div>
            </div>
          </div>
        </section>
      )}

      <details className="mt-8 text-sm text-mute">
        <summary className="cursor-pointer font-bold tracking-wider">DESIGN STATES (PROTOTYPE REVIEW)</summary>
        <div className="mt-3 flex flex-wrap gap-2">
          {([['Empty input', 'empty'], ['Analyzing', 'analyzing'], ['Result layout template', 'results'], ['Model unavailable', 'unavailable'], ['Validation error', 'error']] as [string, State][]).map(([l, st]) => (
            <button key={st} onClick={() => demo(st)} className={`rounded-full border px-3 py-1 font-semibold ${state === st ? 'border-cyan text-cyan' : 'border-line hover:text-ink'}`}>{l}</button>
          ))}
        </div>
      </details>
    </div>
  )
}
