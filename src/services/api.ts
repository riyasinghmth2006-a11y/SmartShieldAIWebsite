/**
 * Centralized API client for SmartShield AI.
 * Handles API URL configuration, safe JSON decoding, network errors, and model status.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8001'
    : '')

export interface HealthStatus {
  status: string
  version: string
  models_configured: {
    scam_heuristic: boolean
    spam_model?: boolean
    fake_news_model?: boolean
    deepfake_model?: boolean
    [key: string]: boolean | undefined
  }
}

export interface IndicatorHit {
  id: string
  label: string
  note: string
}

export interface SpamDetectionResult {
  success: boolean
  label: 'spam' | 'ham'
  confidence: number
  reasons: string[]
  model: string
  hits?: IndicatorHit[]
  level?: string
  explanation?: string
}

export interface ScamDetectionResult {
  success: boolean
  detector: string
  status: string
  level: string
  risk_score: number
  hits: IndicatorHit[]
  model?: string | null
  confidence?: number | null
  explanation: string
  recommendations?: string[]
}

export interface FakeNewsDetectionResult {
  success: boolean
  label: string // 'potentially_false' | 'potentially_authentic' or display string
  confidence?: number | null
  model: string
  explanation: string
  verification_status?: string
  limitations?: string[]
  status?: string
}

export interface DeepfakeDetectionResult {
  success: boolean
  label?: string | null
  confidence?: number | null
  model: string
  explanation: string
  media_summary?: {
    name?: string
    kind?: string
    extension?: string
    mime_type?: string
    size?: string
    bytes?: number
  } | null
  verification_status?: string
  status?: string
}

/**
 * Builds the full endpoint URL respecting VITE_API_BASE_URL or relative fallback.
 */
export function getApiUrl(endpoint: string): string {
  const base = (API_BASE_URL || '').replace(/\/$/, '')
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return base ? `${base}${cleanEndpoint}` : cleanEndpoint
}

/**
 * Safely executes HTTP requests and parses JSON, preventing HTML error page parse failures.
 */
export async function safeFetchJson<T>(endpoint: string, init?: RequestInit): Promise<T> {
  const url = getApiUrl(endpoint)
  let res: Response

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 20000)

  try {
    res = await fetch(url, {
      ...init,
      signal: controller.signal,
    })
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error(`Request to ${endpoint} timed out after 20 seconds.`)
    }
    const msg = err instanceof Error ? err.message : 'Network error'
    throw new Error(`Backend connection failure: Could not reach backend at ${url}. ${msg}`)
  } finally {
    clearTimeout(timeoutId)
  }

  const contentType = res.headers.get('content-type') || ''
  const isJson = contentType.includes('application/json')
  const text = await res.text()

  // Guard against HTML error pages or index.html fallbacks
  if (text.trim().startsWith('<') || (!isJson && text.trim().length > 0)) {
    if (!res.ok) {
      throw new Error(
        `Backend server returned HTTP ${res.status} (${res.statusText || 'Error'}). Please ensure the Python FastAPI server is running on port 8001.`
      )
    }
    throw new Error(
      `Received HTML instead of JSON from ${endpoint}. Please ensure the Python FastAPI server is running on port 8001.`
    )
  }

  let data: any
  try {
    data = JSON.parse(text)
  } catch {
    throw new Error(`Invalid JSON received from backend for ${endpoint}.`)
  }

  if (!res.ok) {
    const detail = data?.detail || data?.error || `Request failed with status ${res.status}`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  return data as T
}

/**
 * Checks system health and model availability.
 */
export async function checkBackendHealth(): Promise<HealthStatus> {
  return safeFetchJson<HealthStatus>('/api/health')
}

/**
 * Evaluates message or URL for spam / scam signals.
 */
export async function detectSpamMessage(text: string): Promise<SpamDetectionResult> {
  return safeFetchJson<SpamDetectionResult>('/api/spam/detect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

export async function analyzeScam(content: string, mode: 'message' | 'url'): Promise<ScamDetectionResult> {
  return safeFetchJson<ScamDetectionResult>('/api/scam/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, mode }),
  })
}

/**
 * Evaluates news article or claim for misinformation patterns.
 */
export async function detectFakeNews(text: string): Promise<FakeNewsDetectionResult> {
  try {
    const data = await safeFetchJson<FakeNewsDetectionResult>('/api/fakenews/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
    return data
  } catch (err: unknown) {
    // Graceful fallback to /api/fake-news/analyze if needed
    try {
      const fallback = await safeFetchJson<any>('/api/fake-news/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const isFake = fallback.label?.toLowerCase().includes('fake')
      return {
        success: fallback.success ?? true,
        label: isFake ? 'potentially_false' : 'potentially_authentic',
        confidence: fallback.confidence,
        model: fallback.model || 'distilbert-fake-news-detector-english',
        explanation: fallback.explanation || '',
        verification_status: 'unverified',
        status: fallback.status,
      }
    } catch {
      throw err
    }
  }
}

/**
 * Inspects uploaded image for deepfake or AI manipulation signatures.
 */
export async function detectDeepfakeImage(file: File): Promise<DeepfakeDetectionResult> {
  const formData = new FormData()
  formData.append('file', file)

  try {
    return await safeFetchJson<DeepfakeDetectionResult>('/api/deepfake/detect', {
      method: 'POST',
      body: formData,
    })
  } catch (err: unknown) {
    // Graceful fallback to /api/deepfake/analyze
    try {
      const fallback = await safeFetchJson<any>('/api/deepfake/analyze', {
        method: 'POST',
        body: formData,
      })
      return {
        success: fallback.success ?? true,
        label: fallback.label,
        confidence: fallback.confidence,
        model: fallback.model || 'vit-deepfake-detector-v2-onnx',
        explanation: fallback.explanation || '',
        media_summary: fallback.media_summary,
        status: fallback.status,
        verification_status: 'unverified',
      }
    } catch {
      throw err
    }
  }
}
