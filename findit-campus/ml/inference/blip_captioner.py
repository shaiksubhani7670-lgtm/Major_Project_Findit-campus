"""
FindIt Campus — BLIP Image Captioner
Uses Salesforce BLIP (blip-image-captioning-base) to auto-generate a
natural-language description from an item photograph.

When to use:
  - A found/lost item has an image uploaded but the user typed a very
    short or empty description (< 30 characters).
  - The generated caption is appended to the existing description before
    SBERT encoding, enriching the text signal.

Graceful degradation:
  - If `transformers` / `torch` are not installed, returns an empty
    string so the pipeline continues without captioning.
  - All model loading is lazy.

Example output:
  Input:  Cloudinary URL of a blue backpack image
  Output: "a blue backpack with multiple pockets on a table"
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

# Minimum description length (chars) to skip BLIP captioning
CAPTION_MIN_DESC_LEN = 30

# Seconds to wait when fetching a remote image
_URL_TIMEOUT = 12


class BLIPCaptioner:
    """
    BLIP-based image-to-text captioner.

    Usage:
        captioner = BLIPCaptioner()
        caption = captioner.caption("https://res.cloudinary.com/.../image.jpg")
        # → "a blue backpack with silver zips"
    """

    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        self.model_name = model_name
        self._processor = None
        self._model = None
        self._available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> bool:
        """Return True if BLIP model is available and loaded."""
        if self._available is not None:
            return self._available

        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration  # type: ignore
            import torch  # type: ignore  # noqa: F401

            self._processor = BlipProcessor.from_pretrained(self.model_name)
            self._model = BlipForConditionalGeneration.from_pretrained(
                self.model_name
            )
            self._model.eval()
            self._available = True
            logger.info(f"[BLIP] Loaded captioning model: {self.model_name}")

        except Exception as exc:
            self._available = False
            logger.warning(
                f"[BLIP] Model not available ({exc}). "
                "Captioning will be skipped."
            )

        return self._available

    # ------------------------------------------------------------------
    # Image loading helper
    # ------------------------------------------------------------------

    @staticmethod
    def _load_pil_image(source: Union[str, bytes, Path]):
        """Load PIL image from URL, local path, or raw bytes. Returns None on failure."""
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

            logger.warning(f"[BLIP] Cannot load image: {source!r}")
            return None

        except Exception as exc:
            logger.warning(f"[BLIP] Image load error: {exc}")
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def caption(
        self,
        image_source: Union[str, bytes, Path],
        max_new_tokens: int = 60,
    ) -> str:
        """
        Generate a natural-language caption from an image.

        Args:
            image_source:   Cloudinary URL, local path, or raw bytes.
            max_new_tokens: Maximum caption length in tokens.

        Returns:
            Caption string (may be empty if BLIP unavailable or image fails).
        """
        if not self._ensure_loaded():
            return ""

        img = self._load_pil_image(image_source)
        if img is None:
            return ""

        try:
            import torch  # type: ignore
            inputs = self._processor(images=img, return_tensors="pt")
            with torch.no_grad():
                out = self._model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    num_beams=4,
                    early_stopping=True,
                )
            caption = self._processor.decode(out[0], skip_special_tokens=True)
            logger.debug(f"[BLIP] Caption: {caption!r}")
            return caption.strip()

        except Exception as exc:
            logger.error(f"[BLIP] Captioning failed: {exc}")
            return ""

    def should_caption(self, existing_description: str) -> bool:
        """
        Return True if BLIP captioning would meaningfully enrich the description.
        Condition: description is shorter than CAPTION_MIN_DESC_LEN characters.
        """
        desc = (existing_description or "").strip()
        return len(desc) < CAPTION_MIN_DESC_LEN

    def enrich_description(
        self,
        existing_description: str,
        image_source: Union[str, bytes, Path, None],
    ) -> tuple[str, bool]:
        """
        Optionally append a BLIP caption to an existing description.

        Args:
            existing_description: The text the user typed.
            image_source:         Image URL/path, or None if no image.

        Returns:
            (enriched_description, caption_was_used)
            - enriched_description: original + " " + caption (if generated)
            - caption_was_used: True if BLIP actually generated something
        """
        if not image_source or not self.should_caption(existing_description):
            return existing_description, False

        cap = self.caption(image_source)
        if not cap:
            return existing_description, False

        combined = f"{existing_description} {cap}".strip()
        logger.info(f"[BLIP] Description enriched: {combined!r}")
        return combined, True

    def is_available(self) -> bool:
        """Return True if BLIP model loaded successfully."""
        return self._ensure_loaded()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

blip_captioner = BLIPCaptioner()
