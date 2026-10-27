# SmartShield AI — Machine Learning Model Artifacts

This directory is designated for trained model weights and vectorizers.

## Supported Model Formats

### 1. Fake News Detection Model

To enable active fake news classification, place your trained model artifacts here:

- `fake_news_model.joblib` — Trained scikit-learn / LightGBM classifier.
- `fake_news_vectorizer.joblib` — Fitted `TfidfVectorizer` or `CountVectorizer`.

*Note: Raw arbitrary `.pkl` files are disallowed for security to prevent unsafe deserialization.*

#### Example Export in Python:
```python
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier

vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7)
X_train_vec = vectorizer.fit_transform(X_train)

model = PassiveAggressiveClassifier(max_iter=50)
model.fit(X_train_vec, y_train)

joblib.dump(model, "backend/models/fake_news_model.joblib")
joblib.dump(vectorizer, "backend/models/fake_news_vectorizer.joblib")
```

### 2. Deepfake Image Detection Model

To enable media classification, place safe ONNX weights here:
- `deepfake_image_model.onnx` — Open Neural Network Exchange standard format (safe graph runtime, no arbitrary code execution).

---

## Behavior When Models Are Missing

By design and policy, SmartShield AI **never fabricates results or invents confidence scores** when trained weights are absent.

If model artifacts are not present:
- The backend automatically returns `{ "status": "model_unavailable", "model_available": false }`.
- The frontend preserves transparency by presenting the user with an honest explanation and recommended external verification steps.
