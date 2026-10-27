# Implementation Plan — Fake News & Deepfake Accuracy Debug & Architecture Repair

This plan outlines the systematic diagnosis, architectural repair, and empirical validation of the Fake News and Deepfake detection systems in SmartShield AI.

---

## 1. Problem Diagnosis & Audit (Phase 1)

### Fake News Detection
- **Issue**: DistilBERT sequence classification models are trained on specific stylistic corpora (e.g., Kaggle Fake News, LIAR) and measure *writing style / linguistic patterns*, not *factual truth*. When genuine news is published with informal vocabulary, breaking-news phrasing, or unfamiliar domains, style classifiers produce false positives.
- **Root Cause**: Relying on style classification alone without checking external empirical evidence causes factually accurate articles to be labeled misleading.
- **Diagnostic Tasks**:
  - Audit `backend/models/fake_news_detector/config.json` (`id2label`, `label2id`, logits).
  - Inspect tokenizer behavior, truncation at 512 tokens, and case normalization.
  - Check fallback paths to ensure exceptions or missing evidence do not default to `potentially_false`.

### Deepfake Detection
- **Issue**: The Vision Transformer model (`dima806/deepfake_vs_real_image_detection` / ViT) was trained on cropped human faces (140,000 real & fake faces dataset). When passed uncropped full-body photos, landscapes, architectural images, animals, or documents, patch extraction evaluates background clutter and reports false positives or arbitrary predictions.
- **Root Cause**: Lack of a face detection and localization pre-stage. Feeding non-face images to a facial deepfake model produces high false-positive rates on real photography.
- **Diagnostic Tasks**:
  - Inspect OpenCV / PIL image loading, dimensions, and color space (`RGB` vs `BGR`).
  - Measure baseline inference on uncropped photos vs. isolated face crops.

---

## 2. Claim-Verification Pipeline for Fake News (Phase 2)

Decouple writing style from factual verification by implementing a structured claim-checking architecture:

1. **Claim Extraction**:
   - Extract key factual assertions, named entities (persons, organizations, places), dates, and core predicates from the input text.
2. **Evidence Retrieval**:
   - Search reliable, independent knowledge sources via Wikipedia REST API (`/api/rest_v1/page/summary/...` and search endpoints) and open web search APIs.
   - Filter retrieved documents for authoritative encyclopedic and primary reporting sources.
3. **Evidence Comparison & Rules**:
   - Compare retrieved facts against the claims (dates, names, event outcomes).
   - Classify claim status into:
     - `VERIFIED`: Multiple authoritative sources corroborate the factual assertions.
     - `LIKELY_FALSE`: Documented contradictions, known hoaxes, or official debunking found.
     - `UNVERIFIED`: Insufficient or inconclusive independent evidence found.
   - **Rule**: Never mark an article false merely because no matching record was found; mark as `UNVERIFIED` with clear disclosure.
   - Return actual source URLs only when they were retrieved and checked.
4. **Integration with Text Classifier**:
   - Report linguistic style confidence separately from factual verification status so users clearly see the distinction.

---

## 3. Deepfake Face Detection & Alignment Pipeline (Phase 3)

Introduce face localization before running facial classification:

1. **Face Detection Stage**:
   - Integrate OpenCV Haar Cascade (`haarcascade_frontalface_default.xml`) / DNN face detector.
   - Check image for human faces:
     - If **no face detected**: Return `INCONCLUSIVE` (`"No human face detected in image. The facial deepfake detector requires clear facial media. Landscapes, documents, or objects cannot be evaluated for facial manipulation."`).
     - If **face(s) detected**: Crop face with contextual padding (20–30% margin) and align for the Vision Transformer input.
2. **Model Preprocessing & Inference**:
   - Resize cropped face to 224×224 bilinear.
   - Normalize with standard ViT parameters (`mean=[0.5, 0.5, 0.5]`, `std=[0.5, 0.5, 0.5]`).
   - Run inference through `dima806/deepfake_vs_real_image_detection`.
   - Calculate softmax probabilities dynamically across `id2label`.
3. **Calibrated Probabilistic Output**:
   - Disclose that results are probabilistic assessments and indicate that non-facial images or non-supported manipulation styles (e.g., full-body re-enactment) are not covered.

---

## 4. Empirical Validation & Held-Out Test Suites (Phase 4)

Build automated test suites with real, independently labeled test samples:

1. **Fake News Evaluation Suite**:
   - Verified genuine news articles (Reuters, BBC, AP).
   - Documented false claims and conspiracy hoaxes.
   - Unfamiliar or emerging claims testing the `UNVERIFIED` state.
   - Metric reporting: Precision, Recall, False-Positive Rate.
2. **Deepfake Evaluation Suite**:
   - Real photographs of people (diverse lighting, resolutions).
   - Real non-facial images (landscapes, objects, cars) verifying `INCONCLUSIVE`.
   - Known AI-generated faces (StyleGAN / Diffusion).
   - Metric reporting: Confusion matrix and False-Positive Rate.

---

## 5. Implementation, Integration & Reporting (Phase 5)

1. Implement `ClaimVerifier` in `backend/services/claim_verification_service.py`.
2. Update `FakeNewsService` to execute claim verification and synthesize results.
3. Implement `FaceDetector` in `backend/services/face_detector.py` and integrate into `DeepfakeService`.
4. Ensure frontend compatibility in `News.tsx` and `Deepfake.tsx` to render `VERIFIED`, `LIKELY_FALSE`, `UNVERIFIED`, and `INCONCLUSIVE` states gracefully.
5. Re-run tests, measure live endpoint responses, and report full results.
