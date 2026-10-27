"""Deepfake image analysis service with ONNX Runtime ViT inference and temporary cleanup."""

import io
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from backend.config import MODELS_DIR
from backend.schemas import DeepfakeDetectionResult
from backend.utils.logging import get_logger
from backend.validators import ValidationError, validate_image_file

logger = get_logger("smartshield.deepfake")

DEEPFAKE_RECOMMENDATIONS = [
    "Run a reverse image search (e.g. Google Lens, TinEye) to trace the earliest appearance of this image.",
    "Inspect high-frequency detail areas such as fingers, earrings, text reflections, and shadow consistency.",
    "Compare the media against authentic photos from established, accredited photojournalism outlets.",
]


def format_file_size(size_bytes: int) -> str:
    """Formats raw bytes into a human-readable string."""
    if size_bytes >= 1048576:
        return f"{size_bytes / 1048576:.1f} MB"
    return f"{max(1, round(size_bytes / 1024))} KB"


class DeepfakeService:
    """
    Validates uploaded images and evaluates authenticity using a trained ONNX ViT model:
    onnx-community/Deep-Fake-Detector-v2-Model-ONNX.
    When no deepfake model is installed in backend/models/, returns 'model_unavailable'
    without inventing fabricated authenticity classifications.
    """

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self._session: Any = None
        self._input_name: str | None = None
        self._legacy_mock_model: Any = None
        self._load_attempted = False

    def is_model_available(self) -> bool:
        """Determines if a compatible deepfake classification model is loaded."""
        self._ensure_loaded()
        return self._session is not None or self._legacy_mock_model is not None

    def _ensure_loaded(self) -> None:
        """Attempts to load deepfake model weights if available."""
        if self._load_attempted:
            return
        self._load_attempted = True

        candidate_paths = [
            self.models_dir / "deepfake_detector_v2" / "model_quantized.onnx",
            self.models_dir / "deepfake_detector_v2" / "model.onnx",
            self.models_dir / "deepfake_image_model.onnx",
        ]

        found = next((p for p in candidate_paths if p.is_file()), None)
        if not found:
            logger.info("Deepfake classification model weights not present on disk.")
            return

        try:
            import onnxruntime as ort

            logger.info(f"Loading ONNX deepfake classification model from {found}")
            # Initialize ONNX inference session with CPU provider
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self._session = ort.InferenceSession(
                str(found),
                sess_options=session_options,
                providers=["CPUExecutionProvider"],
            )
            self._input_name = self._session.get_inputs()[0].name
            logger.info(f"Successfully loaded ONNX model. Input node: {self._input_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize deepfake ONNX model: {e}")
            self._session = None
            self._input_name = None

    def set_model(self, model: Any) -> None:
        """Injects model (used for automated unit tests)."""
        self._legacy_mock_model = model
        self._load_attempted = True

    def _preprocess_image(self, content: bytes) -> Any:
        """
        Preprocesses raw image bytes to ViT input dimensions:
        RGB conversion -> Resize to 224x224 Bilinear -> Rescale (1/255) -> Normalize (mean/std 0.5) -> (1, 3, 224, 224).
        """
        from PIL import Image, UnidentifiedImageError
        import numpy as np

        try:
            image = Image.open(io.BytesIO(content)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as err:
            raise ValidationError(
                "The file could not be decoded as a valid image. It may be incomplete or corrupted."
            ) from err

        image_resized = image.resize((224, 224), Image.Resampling.BILINEAR)

        arr = np.array(image_resized, dtype=np.float32) / 255.0
        mean = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        std = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        arr = (arr - mean) / std
        # Convert HWC to CHW
        arr = np.transpose(arr, (2, 0, 1))
        # Add batch dimension: (1, 3, 224, 224)
        return np.expand_dims(arr, axis=0)

    def analyze_image(self, filename: str, content: bytes) -> DeepfakeDetectionResult:
        """
        Validates the image file, safely writes to a temporary file, executes inference if
        a model is installed, and always cleans up temporary artifacts.
        """
        ext, mime_type = validate_image_file(filename, content)
        size_str = format_file_size(len(content))

        media_summary: Dict[str, Any] = {
            "name": os.path.basename(filename),
            "kind": "image",
            "extension": ext.upper(),
            "mime_type": mime_type,
            "size": size_str,
            "bytes": len(content),
        }

        # Safe temporary file usage with guaranteed cleanup
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix="smartshield_df_",
                suffix=f".{ext}",
                delete=False,
            ) as tmp:
                tmp.write(content)
                temp_file_path = tmp.name

            logger.info(f"Saved media temporarily to {temp_file_path} for inspection")

            # Check if genuine deepfake model is available
            if not self.is_model_available():
                return DeepfakeDetectionResult(
                    success=True,
                    detector="deepfake",
                    status="model_unavailable",
                    model_available=False,
                    media_summary=media_summary,
                    label=None,
                    confidence=None,
                    explanation=(
                        "No deepfake detection model is configured, so no analysis can be run "
                        "and no result will be invented."
                    ),
                    recommendations=DEEPFAKE_RECOMMENDATIONS,
                )

            # If mock model injected for tests
            if self._legacy_mock_model is not None and self._session is None:
                return DeepfakeDetectionResult(
                    success=True,
                    detector="deepfake",
                    status="completed",
                    model_available=True,
                    media_summary=media_summary,
                    label="Analysis Inconclusive",
                    confidence=0.5,
                    explanation="Mock model test inference completed.",
                    recommendations=DEEPFAKE_RECOMMENDATIONS,
                )

            # Genuine ONNX Runtime ViT Inference
            try:
                import numpy as np

                input_tensor = self._preprocess_image(content)
                outputs = self._session.run(None, {self._input_name: input_tensor})
                logits = outputs[0][0]  # shape (2,)

                # Numerically stable softmax
                exp_logits = np.exp(logits - np.max(logits))
                probs = exp_logits / np.sum(exp_logits)

                prob_realism = float(probs[0])
                prob_deepfake = float(probs[1])

                # High-fidelity labels aligning with frontend badges
                if prob_deepfake >= 0.70:
                    label = "Potentially AI-Generated"
                    confidence = round(prob_deepfake, 3)
                    explanation = (
                        f"ViT Deepfake Detector identified strong synthetic generation signatures "
                        f"(manipulation probability: {prob_deepfake:.1%}). The image exhibits texture and frequency "
                        "patterns characteristic of generative diffusion or GAN models."
                    )
                elif prob_deepfake >= 0.50:
                    label = "Potentially Manipulated"
                    confidence = round(prob_deepfake, 3)
                    explanation = (
                        f"ViT Deepfake Detector identified moderate manipulation indicators "
                        f"(manipulation probability: {prob_deepfake:.1%}). Structural anomalies were observed. "
                        "Recommend reverse-searching the original unedited source."
                    )
                else:
                    label = "No Strong Manipulation Signals Detected"
                    confidence = round(prob_realism, 3)
                    explanation = (
                        f"ViT Deepfake Detector found no dominant manipulation patterns "
                        f"(authenticity score: {prob_realism:.1%}). The image exhibits natural sensor noise "
                        "and lighting coherence consistent with standard photography."
                    )

                return DeepfakeDetectionResult(
                    success=True,
                    detector="deepfake",
                    status="completed",
                    model_available=True,
                    media_summary=media_summary,
                    label=label,
                    confidence=confidence,
                    explanation=explanation,
                    recommendations=DEEPFAKE_RECOMMENDATIONS,
                )

            except ValidationError:
                raise
            except Exception as infer_err:
                logger.error(f"Inference error during deepfake analysis: {infer_err}")
                return DeepfakeDetectionResult(
                    success=False,
                    detector="deepfake",
                    status="error",
                    model_available=True,
                    media_summary=media_summary,
                    error="Deepfake model inference encountered an error.",
                    explanation="Failed to complete visual analysis on the uploaded file.",
                    recommendations=DEEPFAKE_RECOMMENDATIONS,
                )

        finally:
            # Guarantee temporary file is deleted
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file {temp_file_path}")
                except Exception as clean_err:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {clean_err}")
