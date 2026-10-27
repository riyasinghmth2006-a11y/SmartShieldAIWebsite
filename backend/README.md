# SmartShield AI — FastAPI Backend Service

Production-ready cybersecurity intelligence and media verification API built with FastAPI, PyTorch, Transformers, ONNX Runtime, and Scikit-Learn.

## Features & Endpoints

| Endpoint | Method | Input | Description | Model Architecture |
|---|---|---|---|---|
| `/api/health` | `GET` | — | System health and model readiness check | — |
| `/api/spam/detect` | `POST` | `{"text": "..."}` | Machine learning spam/ham classification | TF-IDF + Logistic Regression (UCI SMS Spam Collection) |
| `/api/scam/analyze` | `POST` | `{"content": "...", "mode": "message"\|"url"}` | Heuristic urgency, credential, and payment detection | Heuristic rule engine + ML probability |
| `/api/fakenews/detect` | `POST` | `{"text": "..."}` | Fine-tuned DistilBERT fake news classification | DistilBERT (`Lennywinks/fake-news-detector-english`) |
| `/api/fake-news/analyze` | `POST` | `{"text": "..."}` | Legacy fake news article analysis endpoint | DistilBERT Sequence Classifier |
| `/api/deepfake/detect` | `POST` | `multipart/form-data (file)` | Vision Transformer deepfake image detection | ViT ONNX Runtime (`Deep-Fake-Detector-v2-Model-ONNX`) |
| `/api/deepfake/analyze` | `POST` | `multipart/form-data (file)` | Legacy deepfake image inspection endpoint | ViT ONNX Runtime |

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- `pip` and virtual environment support (`python3 -m venv`)

### 2. Install Dependencies
```bash
python3 -m pip install -r backend/requirements.txt
```

### 3. Model Weights Setup
- **Spam Classifier**: Pre-trained TF-IDF vectorizer and Logistic Regression model saved at `backend/models/spam_detector_model.joblib` and `backend/models/spam_vectorizer.joblib`. To retrain:
  ```bash
  python3 backend/train_spam_model.py
  ```
- **Fake News Classifier**: DistilBERT model files in `backend/models/fake_news_detector/` (`config.json`, `model.safetensors`, `tokenizer.json`).
- **Deepfake Classifier**: ViT ONNX quantized model in `backend/models/deepfake_detector_v2/model_quantized.onnx`.

### 4. Running the Backend Server
Run Uvicorn bound to `0.0.0.0:8001`:
```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8001/api/docs`
- OpenAPI JSON: `http://localhost:8001/api/openapi.json`

### 5. Running the Test Suite
```bash
python3 -m pytest backend/tests -v
```
