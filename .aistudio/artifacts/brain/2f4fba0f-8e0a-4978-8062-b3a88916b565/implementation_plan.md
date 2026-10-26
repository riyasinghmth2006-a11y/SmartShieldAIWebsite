# SmartShield AI — Python Backend & ML Architecture

A modular Python FastAPI backend and machine learning service architecture for **SmartShield AI**, connecting to the existing React 19 + Vite frontend via transparent `/api` proxying without modifying visual styling, layout, or components.

## User Review & Critical Decisions

> [!IMPORTANT]
> The architectural direction and scope have been aligned with your preferences:
> - **API Proxying**: Vite server will forward `/api/*` requests to the local Python FastAPI server (`127.0.0.1:8000`), maintaining seamless local development without CORS issues or hardcoded origins.
> - **Fake News Model Strategy**: A strict model loader will safely inspect the `backend/models/` directory for legitimate trained weights and vectorizers. When absent, it returns an explicit `model_unavailable` payload, mapped cleanly into the existing frontend card without fabricating predictions or faking confidence scores.
> - **Deepfake Media Scope**: Targeted validation restricted to images (`PNG, JPG, JPEG, WEBP`), matching the frontend scope while validating file headers and magic bytes to block disguised or corrupted binaries.
> - **Frontend Preservation Guarantee**: The existing UI layout, typography, glassmorphism cards, animations, 3D visual components, navigation frame, and preview controls will be preserved without modification.

---

## 1. Overview & Core Concept

SmartShield AI provides users with guidance on potential digital security threats:
1. **Scam Detection**: High-speed heuristic analysis of suspicious emails, SMS messages, and URLs checking for urgency manipulation, credential theft, payment fraud (gift cards, wire transfers, crypto), and deceptive domain characteristics.
2. **Fake News Detection**: Secure preprocessing and classifier inference interface that inspects article text when a validated trained model is installed, or gracefully informs users when model weights are not loaded.
3. **Deepfake Media Inspection**: Strict image format and magic-byte validation with temporary file cleanup, providing a structured inference hook for deepfake image models and clear status reporting when unconfigured.

---

## 2. User Experience & Visual Design Preservation

All existing visual styling and UI flows are 100% maintained:
- **Zero Redesign**: Navigation tabs, dark navy glassmorphism aesthetic (`bg-bg`, `glass`, `glass-hover`), 3D shield canvas, status pills, and preview control buttons remain intact.
- **Loading & State Continuity**: The frontend's existing `analyzing`, `unavailable`, `error`, and `results` states will be driven by live asynchronous API responses instead of simulated timers (`setTimeout`).
- **Seamless Data Mapping**: Backend response schemas directly match the shape expected by the frontend state stores (e.g., `hits`, `level`, `tone`, `note`, `status`).

---

## 3. Key Product Decisions & Trade-Offs

- **Decision 1: FastAPI for Backend Framework**
  - *Chosen Approach*: Lightweight, high-performance FastAPI service with Pydantic v2 schemas.
  - *Why*: Provides automatic request validation, native type hints, standardized OpenAPI documentation, and asynchronous I/O for file uploads and future ML inferences.
  - *Alternatives Considered*: Flask (requires more boilerplate for schema validation), Streamlit (would replace or collide with the existing React SPA).

- **Decision 2: Strict Model Lifecycle & No Fabricated Results**
  - *Chosen Approach*: If trained model files (e.g. `fake_news_model.joblib` and `fake_news_vectorizer.joblib`) are absent, return `status: "model_unavailable"`.
  - *Why*: Adheres strictly to security integrity and the prompt's instructions: never invent detection results or deceptive confidence values.

- **Decision 3: Server Architecture & Vite Proxy**
  - *Chosen Approach*: The FastAPI app runs on `127.0.0.1:8000`. Vite dev server proxies `/api` to `127.0.0.1:8000`.
  - *Why*: Frontend code only needs to fetch `/api/scam/analyze`, `/api/fake-news/analyze`, and `/api/deepfake/analyze` without CORS headaches or hardcoded absolute URLs.

---

## 4. Technical Architecture & Data Strategy

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       React 19 + Vite                       │
│  (Existing UI: Home, Scam, Fake News, Deepfake, How, About) │
└──────────────────────────────┬──────────────────────────────┘
                               │  fetch('/api/...')
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Vite Dev Server (Port 3000)                 │
│              Proxy rule: /api/* -> 127.0.0.1:8000           │
└──────────────────────────────┬──────────────────────────────┘
                               │  HTTP / JSON & Multipart
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (:8000)                   │
│                                                             │
│   ├── config.py (Settings & Limits)                         │
│   ├── schemas.py (Pydantic Models)                          │
│   ├── validators.py (URL, Text & Magic-Byte Checks)         │
│   │                                                         │
│   └── services/                                             │
│       ├── scam_service.py (Heuristic Rule Engine)           │
│       ├── fake_news_service.py (Preprocess & Model Loader)   │
│       └── deepfake_service.py (Safe Tempfile & Image Scan)  │
└─────────────────────────────────────────────────────────────┘
```

### Proposed Backend Structure

```
backend/
├── __init__.py
├── main.py                  # FastAPI application entrypoint with CORS & routes
├── config.py                # Environment configuration & limits
├── schemas.py               # Shared Pydantic schemas (Scam, News, Deepfake)
├── validators.py            # Sanitization, length limits, file magic checks
├── services/
│   ├── __init__.py
│   ├── scam_service.py      # Rule-based pattern matcher & indicator engine
│   ├── fake_news_service.py # Text cleaner & joblib/pickle model loader
│   └── deepfake_service.py  # Image validator, temporary file handler & model hook
├── models/
│   └── README.md            # Instructions for placing trained ML artifacts
├── utils/
│   ├── __init__.py
│   └── logging.py           # Content-masked logging (privacy preserving)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_scam_service.py
│   ├── test_fake_news_service.py
│   └── test_deepfake_service.py
├── requirements.txt         # fastapi, uvicorn, pydantic, pytest, python-multipart
└── README.md                # Comprehensive setup and PowerShell/Bash instructions
```

### Shared Result Data Schemas

```python
class BaseDetectionResult(BaseModel):
    success: bool
    detector: str
    status: str  # "completed" | "model_unavailable" | "error"
    model_available: bool = False
    explanation: str
    recommendations: list[str] = []
    error: str | None = None

class ScamDetectionResult(BaseDetectionResult):
    level: str             # "None found" | "Some signals" | "Multiple signals"
    risk_score: float      # 0.0 to 1.0
    hits: list[dict[str, str]]  # [{'id': ..., 'label': ..., 'note': ...}]

class FakeNewsDetectionResult(BaseDetectionResult):
    label: str | None = None
    confidence: float | None = None

class DeepfakeDetectionResult(BaseDetectionResult):
    media_summary: dict[str, str] | None = None
    label: str | None = None
```

### API Endpoints
1. `GET /api/health` — Returns system and model availability status.
2. `POST /api/scam/analyze` — Accepts `{ mode: "message" | "url", content: str }`.
3. `POST /api/fake-news/analyze` — Accepts `{ text: str }`.
4. `POST /api/deepfake/analyze` — Accepts multipart form `file: UploadFile`.

### Minimal Frontend Connection (Preserving Existing UI)
- `src/pages/Scam.tsx`: Replaces in-memory `setTimeout` in `run()` with `fetch('/api/scam/analyze', { method: 'POST', ... })`. If backend returns results, populates state identically.
- `src/pages/News.tsx`: Replaces `setTimeout` with `fetch('/api/fake-news/analyze', ...)`. If `status === "model_unavailable"`, sets `setState("unavailable")`.
- `src/pages/Deepfake.tsx`: Replaces `setTimeout` with `fetch('/api/deepfake/analyze', ...)`. Uploads `file` via FormData. If `model_unavailable`, sets `setErr('model')` and `setState('error')`.
- All design states, preview buttons, and error cards are preserved.

---

## 5. Automated Testing Strategy

Pytest test suite under `backend/tests/`:
- **Scam Tests**: High-urgency text, credential requests, crypto payments, deceptive URL structures, benign inputs, oversized inputs, and empty edge cases.
- **Fake News Tests**: Clean text preprocessing, behavior when model artifact is missing (`model_unavailable`), behavior when mock model is injected, and short input validation.
- **Deepfake Tests**: Valid PNG/JPEG uploads, magic-byte mismatch (e.g. executable renamed to `.png`), corrupted image bytes, size threshold enforcement, and cleanup of tempfiles.
