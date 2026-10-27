import { useEffect, useRef, useState } from 'react'
import { I, Ic } from '../components/Visuals'
import { checkBackendHealth, detectFakeNews } from '../services/api'

type State = 'empty' | 'analyzing' | 'results' | 'error' | 'unavailable'
const MAX = 5000
const EXAMPLE = 'Scientists announce miracle fruit that cures every disease overnight, doctors stunned, officials say they are hiding it from the public.'

interface NewsResult {
  label: string
  confidence?: number | null
  model?: string
  explanation?: string
  verification_status?: string
  limitations?: string[]
}

export default function News() {
  const [text, setText] = useState('')
  const [state, setState] = useState<State>('empty')
  const [modelResult, setModelResult] = useState<NewsResult | null>(null)
  const [errorMsg, setErrorMsg] = useState('Please enter at least a full sentence (20+ characters) to analyze.')
  const [unavailableNotice, setUnavailableNotice] = useState({
    title: 'Model currently unavailable',
    desc: 'No trained model is loaded right now, so we cannot produce a prediction. We would rather show nothing than a guess. Cross-check the claim with trusted outlets or a fact-checking organization in the meantime.',
  })
  const isLive = useRef(false)

  useEffect(() => {
    let mounted = true
    checkBackendHealth()
      .then((data) => {
        if (!mounted) return
        if (data.models_configured && !data.models_configured.fake_news_model) {
          setUnavailableNotice({
            title: 'Model currently unavailable',
            desc: 'The DistilBERT fake news classification model is not loaded in memory. Cross-check the claim with trusted news organizations or independent fact-checkers.',
          })
          setState((prev) => (prev === 'empty' ? 'unavailable' : prev))
        }
      })
      .catch((err: unknown) => {
        if (!mounted) return
        const msg = err instanceof Error ? err.message : 'Could not reach backend service.'
        setUnavailableNotice({
          title: 'Backend connection failure',
          desc: msg,
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
    const trimmed = text.trim()
    if (trimmed.length < 20) {
      setErrorMsg('Please enter at least a full sentence (20+ characters) to analyze.')
      return setState('error')
    }
    isLive.current = true
    setState('analyzing')

    try {
      const data = await detectFakeNews(trimmed)
      const isMisleading = data.label === 'potentially_false' || data.label.toLowerCase().includes('fake')
      const displayLabel = isMisleading ? 'Potentially Fake / Misleading' : 'Consistent with Authentic News'

      setModelResult({
        label: displayLabel,
        confidence: data.confidence,
        model: data.model || 'distilbert-fake-news-detector-english',
        explanation: data.explanation || 'Model evaluated stylistic and linguistic patterns in the provided text.',
        verification_status: data.verification_status || 'unverified',
        limitations: data.limitations || [],
      })
      setState('results')
    } catch (err: unknown) {
      setModelResult(null)
      const msg = err instanceof Error ? err.message : 'Analysis failed'
      if (msg.includes('unavailable')) {
        setUnavailableNotice({
          title: 'Model currently unavailable',
          desc: msg,
        })
      } else {
        setUnavailableNotice({
          title: 'Backend connection failure',
          desc: msg,
        })
      }
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
    if (s === 'results') {
      setModelResult({
        label: 'Potentially Fake / Misleading',
        confidence: 0.954,
        model: 'distilbert-fake-news-detector-english',
        explanation: 'DistilBERT evaluated this content and identified linguistic patterns and stylistic features predominantly found in misinformation datasets.',
        verification_status: 'unverified',
        limitations: [],
      })
    }
    setState(s)
  }

  return (
    <div className="fadeup">
      <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">Fake News Detector</h1>
      <p className="mt-3 text-lg text-mute">Examine news claims and article text using fine-tuned DistilBERT machine-learning analysis.</p>

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
            <p role="alert" className="flex items-center gap-2 font-semibold text-rose-400"><Ic d={I.warn} size={16} /> {errorMsg}</p>
          ) : <span />}
          <span className="text-mute">{text.length} / {MAX}</span>
        </div>
        <button onClick={run} disabled={state === 'analyzing'} className="btn-primary mt-5 w-full rounded-xl px-8 py-4 font-bold text-white disabled:opacity-60 sm:w-auto">
          {state === 'analyzing' ? 'Analyzing…' : 'Analyze'}
        </button>
      </section>

      <p className="mt-4 flex gap-3 text-sm text-mute"><span className="text-cyan"><Ic d={I.info} size={18} /></span>Analysis uses a fine-tuned DistilBERT transformer model. Machine-learning results are statistical guidance and never definitive proof that a claim is true or false.</p>

      {state === 'analyzing' && (
        <section className="glass fadeup mt-6 flex items-center gap-5 rounded-3xl p-8" aria-live="polite">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-line border-t-violet" />
          <div>
            <h3 className="text-lg font-bold">Running DistilBERT analysis…</h3>
            <p className="text-sm text-mute">Tokenizing input and computing sequence classification probabilities.</p>
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
          <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
            <div className="glass rounded-3xl p-7">
              <p className="text-xs font-bold tracking-[0.18em] text-mute">MODEL PREDICTION</p>
              <p className={`mt-3 text-3xl font-extrabold ${modelResult?.label.includes('Fake') ? 'text-rose-400' : 'text-emerald-300'}`}>
                {modelResult?.label || 'Classification Complete'}
              </p>
              <p className="mt-3 text-sm leading-relaxed text-mute">
                {modelResult?.confidence !== undefined && modelResult?.confidence !== null
                  ? `Model confidence score: ${(modelResult.confidence * 100).toFixed(1)}%`
                  : 'Confidence score is calculated from softmax logits over the classification head.'}
              </p>
              {modelResult?.model && (
                <div className="mt-4 rounded-xl border border-line bg-bg/50 p-3 text-xs text-mute">
                  <span className="font-bold text-ink">Active Model: </span>
                  <span className="font-mono text-cyan">{modelResult.model}</span>
                </div>
              )}
            </div>
            <div className="glass rounded-3xl p-7">
              <h3 className="text-lg font-extrabold">Explanation</h3>
              <p className="mt-3 text-sm leading-relaxed text-mute">{modelResult?.explanation || 'A plain-language description of what the model examined and what influenced the output.'}</p>

              {modelResult?.limitations && modelResult.limitations.length > 0 && (
                <div className="mt-4 rounded-xl border border-amber-300/40 bg-amber-300/10 p-4 text-sm text-amber-200">
                  <p className="font-bold flex items-center gap-2"><Ic d={I.warn} size={16} /> Language &amp; Model Limitations</p>
                  <ul className="mt-2 list-disc list-inside space-y-1 text-xs text-amber-100">
                    {modelResult.limitations.map((lim, idx) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-6 rounded-xl border border-cyan/30 bg-cyan/5 p-4">
                <p className="font-bold text-cyan">Verify independently</p>
                <p className="mt-1 text-sm leading-relaxed text-mute">An AI classification is statistical guidance based on trained linguistic features, not proof of factual accuracy. Always verify assertions with accredited primary sources and independent fact-checkers before sharing.</p>
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
