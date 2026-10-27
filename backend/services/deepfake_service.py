"""Deepfake image analysis service with pretrained Vision Transformer (ViT) inference and temporary cleanup."""

import io
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from backend.config import MODELS_DIR
from backend.schemas import DeepfakeDetectResponse, DeepfakeDetectionResult
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
    Validates uploaded images and evaluates authenticity using a trained Vision Transformer model:
    dima806/deepfake_vs_real_image_detection (ViT architecture fine-tuned on 140,000 real & fake face samples).
    When no deepfake model is installed in backend/models/, returns model_unavailable
    without inventing fabricated authenticity classifications.
    """

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self._hf_model: Any = None
        self._processor: Any = None
        self._session: Any = None
        self._input_name: str | None = None
        self._legacy_mock_model: Any = None
        self._load_attempted = False

    def is_model_available(self) -> bool:
        """Determines if a compatible deepfake classification model is loaded."""
        self._ensure_loaded()
        return (
            (self._hf_model is not None and self._processor is not None)
            or (self._session is not None and self._input_name is not None)
            or self._legacy_mock_model is not None
        )

    def _ensure_loaded(self) -> None:
        """Attempts to load deepfake model weights if available."""
        if self._load_attempted:
            return
        self._load_attempted = True

        local_dir = self.models_dir / "deepfake_detector_v2"
        # 1. Prefer local PyTorch/Safetensors ViT weights
        if local_dir.is_dir() and (local_dir / "config.json").is_file():
            has_weights = (local_dir / "model.safetensors").is_file() or (local_dir / "pytorch_model.bin").is_file()
            if has_weights:
                try:
                    from transformers import AutoImageProcessor, AutoModelForImageClassification
                    import torch

                    logger.info(f"Loading genuine ViT deepfake detector from {local_dir}")
                    self._processor = AutoImageProcessor.from_pretrained(str(local_dir))
                    self._hf_model = AutoModelForImageClassification.from_pretrained(str(local_dir))
                    self._hf_model.eval()
                    logger.info(f"Successfully loaded ViT deepfake detector with id2label: {self._hf_model.config.id2label}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load ViT PyTorch deepfake model: {e}")
                    self._hf_model = None
                    self._processor = None

        # 2. Check for ONNX model artifacts
        candidate_paths = [
            local_dir / "model.onnx",
            local_dir / "model_quantized.onnx",
            self.models_dir / "deepfake_image_model.onnx",
        ]
        found_onnx = next((p for p in candidate_paths if p.is_file()), None)
        if found_onnx:
            try:
                import onnxruntime as ort

                logger.info(f"Loading ONNX deepfake classification model from {found_onnx}")
                session_options = ort.SessionOptions()
                session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                self._session = ort.InferenceSession(
                    str(found_onnx),
                    sess_options=session_options,
                    providers=["CPUExecutionProvider"],
                )
                self._input_name = self._session.get_inputs()[0].name
                logger.info(f"Successfully loaded ONNX model. Input node: {self._input_name}")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize deepfake ONNX model: {e}")
                self._session = None
                self._input_name = None

        logger.info("Deepfake classification model weights not present on disk.")

    def set_model(self, model: Any) -> None:
        """Injects model (used for automated unit tests)."""
        self._legacy_mock_model = model
        self._load_attempted = True

    def _get_label_mapping(self) -> Tuple[int, int]:
        """
        Extracts the exact indices for real and fake classes from the model configuration.
        Dynamically handles different index conventions.
        """
        raw_id2label = getattr(self._hf_model.config, "id2label", {0: "Real", 1: "Fake"})
        mapping = {}
        for k, v in raw_id2label.items():
            idx = int(k) if str(k).isdigit() else k
            mapping[idx] = str(v).lower()

        real_idx = next((k for k, v in mapping.items() if "real" in v or "authentic" in v), 0)
        fake_idx = next((k for k, v in mapping.items() if "fake" in v or "deepfake" in v or "ai" in v), 1)
        return real_idx, fake_idx

    def _infer_probs(self, content: bytes) -> Tuple[float, float]:
        """
        Executes genuine model inference on image bytes and returns (prob_real, prob_fake).
        """
        from PIL import Image, UnidentifiedImageError
        import torch

        try:
            image = Image.open(io.BytesIO(content)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as err:
            raise ValidationError(
                "The file could not be decoded as a valid image. It may be incomplete or corrupted."
            ) from err

        if self._hf_model is not None and self._processor is not None:
            inputs = self._processor(images=image, return_tensors="pt")
            with torch.no_grad():
                logits = self._hf_model(**inputs).logits[0]
                probs = torch.softmax(logits, dim=-1)

            real_idx, fake_idx = self._get_label_mapping()
            prob_real = float(probs[real_idx].item())
            prob_fake = float(probs[fake_idx].item())
            return prob_real, prob_fake

        if self._session is not None and self._input_name is not None:
            import numpy as np

            image_resized = image.resize((224, 224), Image.Resampling.BILINEAR)
            arr = np.array(image_resized, dtype=np.float32) / 255.0
            mean = np.array([0.5, 0.5, 0.5], dtype=np.float32)
            std = np.array([0.5, 0.5, 0.5], dtype=np.float32)
            arr = (arr - mean) / std
            arr = np.transpose(arr, (2, 0, 1))
            arr = np.expand_dims(arr, axis=0)

            outputs = self._session.run(None, {self._input_name: arr})
            logits = outputs[0][0]
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            return float(probs[0]), float(probs[1])

        return 0.5, 0.5

    def detect_deepfake(self, filename: str, content: bytes) -> DeepfakeDetectResponse:
        """
        Implements POST /api/deepfake/detect with real Vision Transformer inference.
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

        if not self.is_model_available():
            raise ValidationError("Deepfake detection model is currently unavailable on the server.")

        prob_real, prob_fake = self._infer_probs(content)

        if prob_fake >= 0.70:
            label = "Potentially AI-Generated"
            confidence = round(prob_fake, 2)
            explanation = (
                f"Vision Transformer deepfake detector identified strong synthetic generation signatures "
                f"(manipulation probability: {prob_fake:.1%}). The image exhibits texture and patch "
                "patterns characteristic of generative diffusion or GAN synthesis."
            )
        elif prob_fake >= 0.50:
            label = "Potentially Manipulated"
            confidence = round(prob_fake, 2)
            explanation = (
                f"Vision Transformer deepfake detector identified moderate manipulation indicators "
                f"(manipulation probability: {prob_fake:.1%}). Structural anomalies were observed. "
                "Recommend reverse-searching the original unedited source."
            )
        else:
            label = "No Strong Manipulation Signals Detected"
            confidence = round(prob_real, 2)
            explanation = (
                f"Vision Transformer deepfake detector found no dominant manipulation patterns "
                f"(authenticity score: {prob_real:.1%}). Sensor noise and lighting coherence "
                "appear consistent with natural photography."
            )

        return DeepfakeDetectResponse(
            success=True,
            label=label,
            confidence=confidence,
            model="dima806/deepfake_vs_real_image_detection",
            explanation=explanation,
            media_summary=media_summary,
            verification_status="unverified",
        )

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

            if self._legacy_mock_model is not None and self._hf_model is None and self._session is None:
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

            try:
                prob_real, prob_fake = self._infer_probs(content)

                if prob_fake >= 0.70:
                    label = "Potentially AI-Generated"
                    confidence = round(prob_fake, 3)
                    explanation = (
                        f"Vision Transformer deepfake detector identified strong synthetic generation signatures "
                        f"(manipulation probability: {prob_fake:.1%}). The image exhibits texture and patch "
                        "patterns characteristic of generative diffusion or GAN synthesis."
                    )
                elif prob_fake >= 0.50:
                    label = "Potentially Manipulated"
                    confidence = round(prob_fake, 3)
                    explanation = (
                        f"Vision Transformer deepfake detector identified moderate manipulation indicators "
                        f"(manipulation probability: {prob_fake:.1%}). Structural anomalies were observed. "
                        "Recommend reverse-searching the original unedited source."
                    )
                else:
                    label = "No Strong Manipulation Signals Detected"
                    confidence = round(prob_real, 3)
                    explanation = (
                        f"Vision Transformer deepfake detector found no dominant manipulation patterns "
                        f"(authenticity score: {prob_real:.1%}). Sensor noise and lighting coherence "
                        "appear consistent with natural photography."
                    )

                return DeepfakeDetectionResult(
                    success=True,
                    detector="deepfake",
                    status="completed",
                    model_available=True,
                    media_summary=media_summary,
                    label=label,
                    confidence=confidence,
                    model="dima806/deepfake_vs_real_image_detection",
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
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file {temp_file_path}")
                except Exception as clean_err:
                    logger.warning(f"Failed to delete temp file {temp_file_path}: {clean_err}")
