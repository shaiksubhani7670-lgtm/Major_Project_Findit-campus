"""
FindIt Campus — SigLIP Cross-Modal Image Matcher
Uses Google SigLIP (siglip-base-patch16-256) via HuggingFace Transformers.

WHY SIGLIP INSTEAD OF CLIP:
  - SigLIP uses sigmoid loss instead of softmax contrastive loss
  - This means it scores each (image, text) pair INDEPENDENTLY —
    no need for a batch of negatives, no batch-size dependency
  - Result: more reliable similarity scores for individual item pairs
  - +2.3% better zero-shot accuracy vs CLIP ViT-B/32 on ImageNet
  - Especially beneficial for fine-grained item similarity where small
    visual differences (sticker, scratch, zip colour) matter
  - Same compute/memory footprint as original CLIP ViT-B/32

Supported matching modes:
  1. image ↔ image  (both items have photos)
  2. text  ↔ image  (cross-modal: one text, one photo)

Images loaded from:
  - Cloudinary HTTPS URLs (primary storage for this project)
  - Local filesystem paths (tests)
  - Raw bytes

Graceful degradation:
  - Returns 0.5 (neutral) if transformers/torch not installed
  - Returns 0.5 if image URL is unreachable
"""

from __future__ import annotations

import io
import logging
from typing import Optional, Union
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_MAX_IMAGE_SIZE = (256, 256)   # SigLIP base uses 256px patches
_URL_TIMEOUT = 10

# Minimum score to count as a real signal (noise guard from findit_ml pattern)
MIN_SIGLIP_CONFIDENCE: float = 0.25


class SigLIPMatcher:
    """
    Google SigLIP image↔text and image↔image similarity scorer.

    Unlike CLIP which uses a global softmax over a batch, SigLIP scores
    each pair with sigmoid — making it more accurate for single-pair
    item comparison in a lost-and-found context.

    Usage:
        matcher = SigLIPMatcher()
        score = matcher.image_image_similarity(url1, url2)     # 0.0–1.0
        score = matcher.text_image_similarity("blue bag", url)  # 0.0–1.0
    """

    _MODEL_NAME = "google/siglip-base-patch16-256"

    def __init__(self):
        self._processor = None
        self._model = None
        self._available: Optional[bool] = None
        self.dim = 768   # SigLIP base hidden size

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            from transformers import SiglipProcessor, SiglipModel  # type: ignore
            import torch  # type: ignore  # noqa: F401

            self._processor = SiglipProcessor.from_pretrained(self._MODEL_NAME)
            self._model = SiglipModel.from_pretrained(self._MODEL_NAME)
            self._model.eval()
            self._available = True
            logger.info(f"[SigLIP] Loaded: {self._MODEL_NAME}")

        except ImportError:
            # SigLIP classes added in transformers >= 4.41
            # Fall back to CLIP if transformers is old
            try:
                from transformers import CLIPProcessor, CLIPModel  # type: ignore
                import torch  # type: ignore  # noqa: F401
                logger.warning(
                    "[SigLIP] SiglipModel not found in your transformers version. "
                    "Falling back to CLIP ViT-B/32. "
                    "Run: pip install transformers>=4.41 to enable SigLIP."
                )
                self._processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                self._model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self._model.eval()
                self._available = True
                self._using_clip_fallback = True
                logger.info("[SigLIP] CLIP fallback loaded.")
            except Exception as exc2:
                self._available = False
                logger.warning(
                    f"[SigLIP] Neither SigLIP nor CLIP available ({exc2}). "
                    "Image matching returns neutral 0.5."
                )
        except Exception as exc:
            self._available = False
            logger.warning(f"[SigLIP] Model not available ({exc}). Returns 0.5 (neutral).")

        return self._available

    # ------------------------------------------------------------------
    # Image loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_pil_image(source: Union[str, bytes, Path]):
        """Load PIL image from URL, path, or bytes. Returns None on failure."""
        try:
            from PIL import Image  # type: ignore

            if isinstance(source, (bytes, bytearray)):
                return Image.open(io.BytesIO(source)).convert("RGB")

            source = str(source)

            if source.startswith("http://") or source.startswith("https://"):
                import requests  # type: ignore
                resp = requests.get(source, timeout=_URL_TIMEOUT, stream=True)
                resp.raise_for_status()
                return Image.open(io.BytesIO(resp.content)).convert("RGB")

            if Path(source).is_file():
                return Image.open(source).convert("RGB")

            logger.debug(f"[SigLIP] Cannot load image source: {source!r}")
            return None

        except Exception as exc:
            logger.debug(f"[SigLIP] Image load failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # Encoding — SigLIP-specific
    # ------------------------------------------------------------------

    def _encode_image(self, image_source) -> Optional[np.ndarray]:
        """Return normalised image embedding or None."""
        if not self._ensure_loaded():
            return None

        img = self._load_pil_image(image_source)
        if img is None:
            return None

        try:
            import torch  # type: ignore
            # SigLIP uses [0.5, 0.5, 0.5] normalisation (handled by processor)
            inputs = self._processor(images=img, return_tensors="pt")
            with torch.no_grad():
                if hasattr(self._model, "get_image_features"):
                    feats = self._model.get_image_features(**inputs)
                else:
                    feats = self._model.vision_model(**inputs).pooler_output
            vec = feats.squeeze().cpu().numpy().astype(np.float32)
            return self._l2_norm(vec)
        except Exception as exc:
            logger.error(f"[SigLIP] Image encoding failed: {exc}")
            return None

    def _encode_text(self, text: str) -> Optional[np.ndarray]:
        """Return normalised text embedding or None."""
        if not self._ensure_loaded():
            return None
        if not text or not text.strip():
            return None

        try:
            import torch  # type: ignore
            inputs = self._processor(
                text=[text], return_tensors="pt", padding="max_length", truncation=True
            )
            with torch.no_grad():
                if hasattr(self._model, "get_text_features"):
                    feats = self._model.get_text_features(**inputs)
                else:
                    feats = self._model.text_model(**inputs).pooler_output
            vec = feats.squeeze().cpu().numpy().astype(np.float32)
            return self._l2_norm(vec)
        except Exception as exc:
            logger.error(f"[SigLIP] Text encoding failed: {exc}")
            return None

    @staticmethod
    def _l2_norm(vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two already-normalised vectors → dot product."""
        return float(max(0.0, min(1.0, np.dot(a, b))))

    # ------------------------------------------------------------------
    # SigLIP pairwise sigmoid score (the key advantage over CLIP)
    # ------------------------------------------------------------------

    def _siglip_pair_score(
        self,
        image_source=None,
        text: str = "",
    ) -> float:
        """
        Compute a SigLIP sigmoid score for a single (image, text) pair.
        This is the methodologically correct way to use SigLIP —
        it doesn't need a batch of negatives like CLIP does.
        Returns a value in [0, 1] where 1 = perfect match.
        """
        if not self._ensure_loaded():
            return 0.5

        img = self._load_pil_image(image_source) if image_source else None
        if img is None or not text:
            return 0.5

        try:
            import torch  # type: ignore

            # Check if we have true SigLIP (not CLIP fallback)
            if hasattr(self._model, "logit_scale") and not getattr(self, "_using_clip_fallback", False):
                # True SigLIP: forward pass computes sigmoid logits directly
                inputs = self._processor(
                    text=[text], images=img, return_tensors="pt", padding="max_length", truncation=True
                )
                with torch.no_grad():
                    out = self._model(**inputs)
                    # SigLIP outputs logits_per_image shaped (1, 1) for single pair
                    logits = out.logits_per_image
                    score = float(torch.sigmoid(logits).squeeze().cpu())
                return max(0.0, min(1.0, score))
            else:
                # CLIP fallback: use cosine similarity
                img_vec = self._encode_image(image_source)
                txt_vec = self._encode_text(text)
                if img_vec is None or txt_vec is None:
                    return 0.5
                return self._cosine(img_vec, txt_vec)

        except Exception as exc:
            logger.debug(f"[SigLIP] Pair score failed: {exc}")
            # Fallback to cosine-based scoring
            img_vec = self._encode_image(image_source)
            txt_vec = self._encode_text(text)
            if img_vec is None or txt_vec is None:
                return 0.5
            return self._cosine(img_vec, txt_vec)

    # ------------------------------------------------------------------
    # Public API (same interface as old CLIPMatcher for compatibility)
    # ------------------------------------------------------------------

    def image_image_similarity(
        self,
        image_source_1: Union[str, bytes, Path],
        image_source_2: Union[str, bytes, Path],
    ) -> float:
        """
        Compute visual similarity between two images.

        Args:
            image_source_1: URL / path / bytes of image 1 (lost item)
            image_source_2: URL / path / bytes of image 2 (found item)

        Returns:
            float in [0.0, 1.0]. Returns 0.5 if unavailable.
        """
        if not self._ensure_loaded():
            return 0.5

        vec1 = self._encode_image(image_source_1)
        vec2 = self._encode_image(image_source_2)

        if vec1 is None or vec2 is None:
            return 0.5

        score = self._cosine(vec1, vec2)
        logger.debug(f"[SigLIP] image↔image: {score:.4f}")
        return score

    def text_image_similarity(
        self,
        text: str,
        image_source: Union[str, bytes, Path],
    ) -> float:
        """
        Compute cross-modal similarity: item description ↔ photo.

        Uses SigLIP's sigmoid pair score (more accurate than CLIP cosine
        for single-pair evaluation without a batch of negatives).

        Returns:
            float in [0.0, 1.0]. Returns 0.5 if unavailable.
        """
        if not text or not text.strip():
            return 0.5

        score = self._siglip_pair_score(image_source=image_source, text=text.strip())
        logger.debug(f"[SigLIP] text↔image: {score:.4f}")
        return score

    def encode_image(self, image_source) -> np.ndarray:
        """Return SigLIP image embedding. Zero-vector if unavailable."""
        if not self._ensure_loaded():
            return np.zeros(self.dim, dtype=np.float32)
        vec = self._encode_image(image_source)
        if vec is None:
            return np.zeros(self.dim, dtype=np.float32)
        # Pad/trim to self.dim if needed (SigLIP base is 768, CLIP fallback is 512)
        if vec.shape[0] != self.dim:
            out = np.zeros(self.dim, dtype=np.float32)
            n = min(vec.shape[0], self.dim)
            out[:n] = vec[:n]
            return out
        return vec

    def encode_text(self, text: str) -> np.ndarray:
        """Return SigLIP text embedding. Zero-vector if unavailable."""
        if not self._ensure_loaded():
            return np.zeros(self.dim, dtype=np.float32)
        vec = self._encode_text(text)
        if vec is None:
            return np.zeros(self.dim, dtype=np.float32)
        if vec.shape[0] != self.dim:
            out = np.zeros(self.dim, dtype=np.float32)
            n = min(vec.shape[0], self.dim)
            out[:n] = vec[:n]
            return out
        return vec

    def is_available(self) -> bool:
        return self._ensure_loaded()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
siglip_matcher = SigLIPMatcher()

# Backward-compatible alias — any code importing clip_matcher still works
clip_matcher = siglip_matcher
