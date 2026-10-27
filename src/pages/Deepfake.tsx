import { useEffect, useRef, useState } from 'react'
import { I, Ic, Shield3D } from '../components/Visuals'
import { checkBackendHealth, detectDeepfakeImage } from '../services/api'

type State = 'empty' | 'selected' | 'analyzing' | 'results' | 'error'
type ErrKind = 'type' | 'size' | 'unsupported' | 'model' | 'connection'
type Picked = { name: string; kind: 'image'; ext: string; size: string; url?: string }

const IMG = ['png', 'jpg', 'jpeg', 'webp']
const DISCLAIMER = 'AI media detection evaluates frequency and structural consistency patterns. Results are statistical indicators, not definitive proof of authenticity or manipulation.'

const ERRORS: Record<ErrKind, { t: string; d: string }> = {
  type: { t: 'Invalid file type', d: 'This file is not one of the supported image formats. Please upload a PNG, JPG, JPEG, or WEBP file.' },
  size: { t: 'File too large', d: 'The uploaded image exceeds the maximum allowed size of 10 MB. Please choose a smaller image.' },
  unsupported: { t: 'Unsupported media', d: 'The file could not be decoded as a valid image. It may be incomplete, corrupted, or have invalid headers.' },
  model: { t: 'Analysis unavailable', d: 'The Vision Transformer deepfake detection model is not loaded in memory on the backend.' },
  connection: { t: 'Backend connection failure', d: 'Could not connect to the backend server. Please ensure the Python FastAPI server is running on port 8001.' },
}

const fmt = (b: number) => (b > 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`)

function Frame({ file, scanning }: { file: Picked | null; scanning?: boolean }) {
  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-2xl border border-cyan/30 bg-bg/80">
      {file?.url && <img src={file.url} alt="Selected file preview" className="h-full w-full object-contain" />}
      {file && !file.url && (
        <div className="grid h-full place-items-center text-mute"><Ic d={I.media} size={44} /></div>
      )}
      {scanning && (
        <>
          <div className="absolute inset-x-0 h-0.5 animate-[scan_1.8s_ease-in-out_infinite_alternate] bg-cyan shadow-[0_0_18px_4px_#22d3ee]" style={{ top: 0 }} />
          <div className="absolute inset-0 bg-gradient-to-b from-cyan/10 to-transparent" />
        </>
      )}
      <span className="absolute left-3 top-3 h-4 w-4 border-l-2 border-t-2 border-cyan" />
      <span className="absolute right-3 top-3 h-4 w-4 border-r-2 border-t-2 border-cyan" />
      <span className="absolute bottom-3 left-3 h-4 w-4 border-b-2 border-l-2 border-cyan" />
      <span className="absolute bottom-3 right-3 h-4 w-4 border-b-2 border-r-2 border-cyan" />
    </div>
  )
}

export default function Deepfake() {
  const [state, setState] = useState<State>('empty')
  const [file, setFile] = useState<Picked | null>(null)
  const [rawFile, setRawFile] = useState<File | null>(null)
  const [modelResult, setModelResult] = useState<{ label?: string | null; confidence?: number | null; model?: string; explanation?: string } | null>(null)
  const [err, setErr] = useState<ErrKind>('type')
  const [customErrorDesc, setCustomErrorDesc] = useState<string | null>(null)
  const [drag, setDrag] = useState(false)
  const imgRef = useRef<HTMLInputElement>(null)

  useEffect(() => () => { if (file?.url) URL.revokeObjectURL(file.url) }, [file])

  useEffect(() => {
    let mounted = true
    checkBackendHealth()
      .then((data) => {
        if (!mounted) return
        if (data.models_configured && !data.models_configured.deepfake_model) {
          setErr('model')
        }
      })
      .catch((err: unknown) => {
        if (!mounted) return
        setErr('connection')
        const msg = err instanceof Error ? err.message : null
        setCustomErrorDesc(msg)
        setState((prev) => (prev === 'empty' ? 'error' : prev))
      })
    return () => {
      mounted = false
    }
  }, [])

  const pick = (f?: File) => {
    if (!f) return
    const ext = f.name.split('.').pop()?.toLowerCase() ?? ''
    if (!IMG.includes(ext)) {
      setFile(null)
      setRawFile(null)
      setErr('type')
      setCustomErrorDesc(null)
      return setState('error')
    }
    if (f.size > 10 * 1024 * 1024) {
      setFile(null)
      setRawFile(null)
      setErr('size')
      setCustomErrorDesc(null)
      return setState('error')
    }
    setRawFile(f)
    setFile({ name: f.name, ext: ext.toUpperCase(), kind: 'image', size: fmt(f.size), url: URL.createObjectURL(f) })
    setState('selected')
  }

  const clear = () => {
    setFile(null)
    setRawFile(null)
    setModelResult(null)
    setCustomErrorDesc(null)
    setState('empty')
  }

  const analyzeMedia = async () => {
    if (!rawFile) return
    setState('analyzing')
    setCustomErrorDesc(null)

    try {
      const data = await detectDeepfakeImage(rawFile)
      if (data.success && data.label) {
        setModelResult({
          label: data.label,
          confidence: data.confidence,
          model: data.model || 'vit-deepfake-detector-v2-onnx',
          explanation: data.explanation,
        })
        setState('results')
      } else {
        setModelResult(null)
        setErr('model')
        setState('error')
      }
    } catch (err: unknown) {
      setModelResult(null)
      const msg = err instanceof Error ? err.message : ''
      if (msg.includes('file type') || msg.includes('extension')) setErr('type')
      else if (msg.includes('exceeds maximum allowed') || msg.includes('size')) setErr('size')
      else if (msg.includes('decoded') || msg.includes('corrupted') || msg.includes('format headers')) setErr('unsupported')
      else if (msg.includes('unavailable')) setErr('model')
      else setErr('connection')

      if (msg) setCustomErrorDesc(msg)
      setState('error')
    }
  }

  const demo = (s: State, e?: ErrKind) => {
    setModelResult(null)
    setCustomErrorDesc(null)
    if (e) setErr(e)
    if (s === 'empty') { setFile(null); setRawFile(null) }
    else if (!file) setFile({ name: 'sample_face_check.png', kind: 'image', ext: 'PNG', size: '1.4 MB' })
    if (s === 'results') {
      setModelResult({
        label: 'Potentially AI-Generated',
        confidence: 0.942,
        model: 'vit-deepfake-detector-v2-onnx',
        explanation: 'ViT Deepfake Detector identified high synthetic generation signatures. Textural anomalies and frequency inconsistencies suggest diffusion or GAN generation.',
      })
    }
    setState(s)
  }

  const inputs = (
    <input ref={imgRef} type="file" hidden accept=".png,.jpg,.jpeg,.webp" onChange={(e) => { pick(e.target.files?.[0]); e.target.value = '' }} />
  )
  const replace = () => imgRef.current?.click()

  return (
    <div className="fadeup">
      <h1 className="text-4xl font-extrabold tracking-tight md:text-5xl">Deepfake Detector</h1>
      <p className="mt-3 text-lg text-mute">Inspect images for visual and structural signs of AI generation or deepfake manipulation using Vision Transformer analysis.</p>
      <p className="mt-4 inline-flex items-center gap-2 rounded-full border border-cyan/40 bg-cyan/10 px-4 py-1.5 text-xs font-bold tracking-wider text-cyan">
        LIVE INFERENCE · PRETRAINED VIT ONNX RUNTIME ENGINE
      </p>
      {inputs}

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_300px]">
        <section className="glass rounded-3xl p-5 md:p-7">
          {(state === 'empty' || (state === 'error' && !file)) && (
            <div
              onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
              onDragLeave={() => setDrag(false)}
              onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]) }}
              className={`flex flex-col items-center rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors ${drag ? 'border-cyan bg-cyan/10' : 'border-line bg-bg/40'}`}
            >
              <span className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-blue/50 to-[#0a2a66] text-ink shadow-[0_12px_24px_-8px_rgba(22,133,255,.6)]"><Ic d={I.upload} size={30} /></span>
              <h3 className="mt-5 text-xl font-extrabold">Drag and drop an image here</h3>
              <p className="mt-2 text-sm text-mute">or choose a file from your device</p>
              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <button onClick={() => imgRef.current?.click()} className="btn-primary rounded-xl px-6 py-3.5 font-bold text-white">Upload Image</button>
              </div>
              <dl className="mt-7 space-y-1 text-sm text-mute">
                <div><dt className="inline font-bold text-ink">Supported formats: </dt><dd className="inline">PNG, JPG, JPEG, WEBP</dd></div>
                <div><dt className="inline font-bold text-ink">Max file size: </dt><dd className="inline">10 MB</dd></div>
              </dl>
            </div>
          )}

          {file && state !== 'results' && (state !== 'error' || file) && (
            <div>
              <Frame file={file} scanning={state === 'analyzing'} />
              <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate font-bold">{file.name}</p>
                  <p className="text-sm text-mute">Image · {file.ext} · {file.size}</p>
                </div>
                {state === 'selected' && (
                  <div className="flex gap-2 text-sm font-bold">
                    <button onClick={replace} className="rounded-lg border border-line px-4 py-2 hover:border-cyan/60">Replace</button>
                    <button onClick={clear} className="rounded-lg border border-line px-4 py-2 text-rose-300 hover:border-rose-400/60">Remove</button>
                  </div>
                )}
              </div>
            </div>
          )}

          {state === 'analyzing' && (
            <div className="mt-6 flex items-center gap-4" aria-live="polite">
              <div className="h-11 w-11 animate-spin rounded-full border-4 border-line border-t-cyan" />
              <div>
                <h3 className="text-lg font-bold">Analyzing Media...</h3>
                <p className="text-sm text-mute">Executing Vision Transformer patch extraction and manipulation analysis.</p>
              </div>
            </div>
          )}

          {state === 'error' && (
            <div role="alert" className="mt-6 rounded-2xl border border-rose-400/40 bg-rose-400/10 p-5">
              <p className="flex items-center gap-2 font-extrabold text-rose-300"><Ic d={I.warn} size={20} /> {ERRORS[err].t}</p>
              <p className="mt-2 text-sm leading-relaxed text-mute">{customErrorDesc || ERRORS[err].d}</p>
              <button onClick={() => (file ? setState('selected') : clear())} className="mt-4 rounded-lg border border-line px-4 py-2 text-sm font-bold hover:border-cyan/60">Retry</button>
            </div>
          )}

          {state === 'results' && (
            <div>
              <div className="flex items-center gap-4">
                <div className="w-40 shrink-0"><Frame file={file} /></div>
                <div className="min-w-0 text-sm text-mute">
                  <p className="font-bold text-ink">Image Summary</p>
                  <p className="truncate">{file?.name} · Image · {file?.ext} · {file?.size}</p>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <button onClick={analyzeMedia} disabled={!file || state === 'analyzing' || state === 'results'} className="btn-primary rounded-xl px-8 py-4 font-bold text-white disabled:cursor-not-allowed disabled:opacity-40">Analyze Media</button>
            <button onClick={clear} disabled={!file} className="rounded-xl border border-line px-8 py-4 font-bold transition-colors hover:border-cyan/60 disabled:cursor-not-allowed disabled:opacity-40">Clear File</button>
          </div>
        </section>

        <aside className="glass relative flex flex-col items-center overflow-hidden rounded-3xl p-6 text-center">
          <div className="relative mt-2 w-full max-w-[220px]">
            <div className="aspect-[4/3] w-full rounded-xl border border-cyan/40 bg-gradient-to-br from-blue/20 to-violet/20 [transform:perspective(500px)_rotateY(-14deg)]">
              <div className="absolute inset-x-3 h-0.5 animate-[scan_2.4s_ease-in-out_infinite_alternate] bg-cyan shadow-[0_0_16px_3px_#22d3ee]" />
              <div className="grid h-full place-items-center text-cyan/70"><Ic d={I.media} size={44} /></div>
            </div>
            <div className="absolute -bottom-6 -right-4"><Shield3D size={96} lock={false} /></div>
          </div>
          <h3 className="mt-10 text-lg font-extrabold">Look closer, verify further</h3>
          <p className="mt-2 text-sm leading-relaxed text-mute">Media analysis highlights possible signals. It cannot prove how a file was made.</p>
        </aside>
      </div>

      {state === 'results' && (
        <section className="fadeup mt-6 space-y-6">
          <div className="glass rounded-3xl p-7">
            <p className="text-xs font-bold tracking-[0.18em] text-mute">RESULT CLASSIFICATION</p>
            <p className="mt-3 text-3xl font-extrabold text-ink">{modelResult?.label || 'Analysis Complete'}</p>
            <div className="mt-5 flex flex-wrap gap-2 text-xs font-bold">
              <span className={`rounded-full border px-3 py-1 ${modelResult?.label === 'Potentially AI-Generated' ? 'border-rose-400 bg-rose-400/30 text-rose-300 font-extrabold ring-1 ring-rose-400' : 'border-rose-400/40 bg-rose-400/10 text-rose-300'}`}>Potentially AI-Generated</span>
              <span className={`rounded-full border px-3 py-1 ${modelResult?.label === 'Potentially Manipulated' ? 'border-amber-300 bg-amber-300/30 text-amber-300 font-extrabold ring-1 ring-amber-300' : 'border-amber-300/40 bg-amber-300/10 text-amber-300'}`}>Potentially Manipulated</span>
              <span className={`rounded-full border px-3 py-1 ${modelResult?.label === 'No Strong Manipulation Signals Detected' ? 'border-emerald-400 bg-emerald-400/30 text-emerald-300 font-extrabold ring-1 ring-emerald-400' : 'border-emerald-400/40 bg-emerald-400/10 text-emerald-300'}`}>No Strong Manipulation Signals Detected</span>
            </div>
            <div className="mt-5 h-2.5 rounded-full bg-line"><div className="h-full rounded-full bg-cyan transition-all duration-500" style={{ width: modelResult?.confidence ? `${Math.round(modelResult.confidence * 100)}%` : '0%' }} /></div>
            <p className="mt-2 text-xs text-mute">Risk indicator. Populated directly from ViT ONNX model output.{modelResult?.confidence ? ` Model confidence score: ${(modelResult.confidence * 100).toFixed(1)}%` : ''}</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {[
              ['Detected Indicators', 'Visual frequency and structural consistency patterns evaluated across 16x16 pixel patches by Vision Transformer (ViT).'],
              ['Analysis Explanation', modelResult?.explanation || 'A short description of what was examined and how to read the outcome.'],
              ['Recommended Next Steps', 'Find the original source, run a reverse image search (e.g. Google Lens, TinEye), and compare with authentic photo archives.'],
              ['Model Status', `Active (${modelResult?.model || 'ViT Deepfake Detector v2 - ONNX Quantized'})`],
            ].map(([t, d]) => (
              <div key={t} className="glass rounded-3xl p-6">
                <h3 className="font-extrabold">{t}</h3>
                <p className="mt-2 text-sm leading-relaxed text-mute">{d}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <p className="mt-6 flex gap-3 rounded-xl border border-line bg-bg2/70 p-4 text-sm text-mute"><span className="text-cyan"><Ic d={I.info} size={18} /></span>{DISCLAIMER}</p>

      <details className="mt-8 text-sm text-mute">
        <summary className="cursor-pointer font-bold tracking-wider">DESIGN STATES (PROTOTYPE REVIEW)</summary>
        <div className="mt-3 flex flex-wrap gap-2">
          {([['Empty', 'empty'], ['File selected', 'selected'], ['Analyzing', 'analyzing'], ['Results template', 'results']] as [string, State][]).map(([l, s]) => (
            <button key={s} onClick={() => demo(s)} className={`rounded-full border px-3 py-1 font-semibold ${state === s ? 'border-cyan text-cyan' : 'border-line hover:text-ink'}`}>{l}</button>
          ))}
          {(Object.keys(ERRORS) as ErrKind[]).map((k) => (
            <button key={k} onClick={() => demo('error', k)} className={`rounded-full border px-3 py-1 font-semibold ${state === 'error' && err === k ? 'border-rose-400 text-rose-300' : 'border-line hover:text-ink'}`}>Error: {ERRORS[k].t}</button>
          ))}
        </div>
      </details>
    </div>
  )
}
