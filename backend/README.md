# SmartShield AI — Backend Architecture & Service Documentation

SmartShield AI provides a separate, maintainable Python backend designed to handle security analysis, validation, and machine-learning model inference for three capabilities:
1. **Scam Detection** (Heuristic rule engine)
2. **Fake News Detection** (ML classifier interface with preprocessing)
3. **Deepfake Media Inspection** (Secure image integrity verification & model interface)

---

## 1. Directory Structure & Responsibilities

```
backend/
├── __init__.py              # Package version and export definitions
├── main.py                  # FastAPI application, CORS, exception handlers & routing
├── config.py                # Environment configuration, port binding & input thresholds
├── schemas.py               # Shared Pydantic schemas across all detector endpoints
├── validators.py            # Input sanitization, length boundaries & magic-byte validation
├── services/
│   ├── __init__.py          # Service exports
│   ├── scam_service.py      # Urgency, credential theft, payment fraud & URL heuristics
│   ├── fake_news_service.py # Text normalization & scikit-learn/joblib model loader
│   └── deepfake_service.py  # Image validation, safe tempfile handling & inference hook
├── models/
│   └── README.md            # Drop-in guide for trained classification artifacts
├── utils/
│   ├── __init__.py
│   └── logging.py           # Privacy-safe logger that redacts sensitive customer data
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and FastAPI TestClient setup
│   ├── test_scam_service.py # Urgency, payment, credentials, URLs & edge-case tests
│   ├── test_fake_news_service.py # Preprocessing & missing-model transparency tests
│   └── test_deepfake_service.py  # Magic-byte integrity, size limits & path traversal tests
├── requirements.txt         # Production and testing Python dependencies
└── README.md                # System documentation
```

---

## 2. Installation & Prerequisites

Python 3.10+ is required.

### Linux / macOS
```bash
# 1. Create a virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt
```

### Windows (PowerShell)
```powershell
# 1. Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r backend/requirements.txt
```

---

## 3. Running the Backend Server

The FastAPI backend runs on `127.0.0.1:8001` (to prevent conflicts with common container control plane ports).

### Linux / macOS
```bash
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

### Windows (PowerShell)
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload
```

Interactive Swagger API documentation is available at `http://127.0.0.1:8001/api/docs`.

---

## 4. How the Frontend Connects

The React + Vite frontend runs on port `3000`. In `vite.config.ts`, requests matching `/api/*` are automatically proxied to `http://127.0.0.1:8001`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8001',
      changeOrigin: true,
    },
  },
}
```

This guarantees:
- No CORS errors during local development.
- The frontend codebase uses simple relative paths (`fetch('/api/scam/analyze', ...)`).
- Visual layouts, typography, 3D elements, and design states remain 100% intact.

---

## 5. Machine Learning Models & Architecture

SmartShield AI integrates genuine open-source pretrained models stored locally in `backend/models/`:

### 1. Fake News Classifier (`backend/models/fake_news_detector/`)
- **Model**: `Lennywinks/fake-news-detector-english`
- **Architecture**: `DistilBertForSequenceClassification` (`distilbert-base-cased` fine-tuned on 63k English articles from WELFake and WebzIO).
- **License**: MIT
- **Task**: Binary text classification (`0: fake`, `1: real`).
- **Inference Runtime**: Hugging Face `transformers` + PyTorch CPU (`AutoModelForSequenceClassification`). Max token length: 512.
- **Label Mapping**:
  - `fake` -> `"Potentially Fake / Misleading"`
  - `real` -> `"Consistent with Authentic News"`
- **Fallback**: If the directory is removed, the service returns `status: "model_unavailable"` without guessing.

### 2. Deepfake Image Detector (`backend/models/deepfake_detector_v2/`)
- **Model**: `onnx-community/Deep-Fake-Detector-v2-Model-ONNX`
- **Architecture**: ViT (`ViTForImageClassification`, base `prithivMLmods/Deep-Fake-Detector-v2-Model`).
- **License**: Apache 2.0
- **Task**: Binary image classification (`0: Realism`, `1: Deepfake`).
- **Format**: Standard ONNX model (`model_quantized.onnx`, 83.3 MB int8 quantized for fast CPU inference).
- **Inference Runtime**: Python `onnxruntime` with `CPUExecutionProvider`.
- **Preprocessing Pipeline**:
  - Convert to RGB
  - Bilinear resize to 224x224
  - Rescale `1/255`
  - Normalize with `mean=[0.5, 0.5, 0.5]`, `std=[0.5, 0.5, 0.5]`
  - Tensor shape: `(1, 3, 224, 224)` float32
- **Label Mapping**:
  - Manipulation probability >= 70%: `"Potentially AI-Generated"`
  - Manipulation probability 50-70%: `"Potentially Manipulated"`
  - Authenticity probability > 50%: `"No Strong Manipulation Signals Detected"`
- **Fallback**: If the ONNX file is removed, the service returns `status: "model_unavailable"`.


---

## 6. Running Automated Tests

Run the full automated test suite (20+ tests covering input validation, heuristic patterns, tempfile cleanup, model absence, and REST endpoints):

### Linux / macOS
```bash
python3 -m pytest backend/tests/ -v
```

### Windows (PowerShell)
```powershell
python -m pytest backend/tests/ -v
```

---

## 7. Known Limitations

1. **Heuristic Scam Detection**: Rule-based checks detect known patterns (urgency, credential harvesting, unusual payment, suspicious TLDs). Novel or sophisticated social-engineering attacks may not trigger these indicators.
2. **Model Availability**: The fake news and deepfake detectors require genuine pre-trained weights in `backend/models/` to perform inferences. They will honestly report `model_unavailable` when unconfigured.
3. **Stateless Operation**: By design, no databases or persistent user accounts are introduced. Media files are handled in ephemeral temporary memory and cleaned up immediately after inspection.
