"""
FindIt Campus — BGE Semantic Text Embedder
Primary text-matching engine using BAAI/bge-small-en-v1.5.

WHY BGE INSTEAD OF ALL-MINILM-L6-V2:
  - Same 384-dim output → zero FAISS index changes needed
  - Outperforms MiniLM-L6-v2 by ~10% on MTEB retrieval benchmarks
  - Instruction-tuned: uses a query prefix for retrieval tasks so the
    model understands it should SEARCH, not just encode
  - Modern (2023) vs MiniLM (2021): trained on far larger, higher-
    quality contrastive pairs

Instruction prefix (crucial for BGE accuracy):
  - Queries (the new report being matched):
    "Represent this sentence for searching relevant passages: {text}"
  - Corpus (indexed candidates): no prefix

Graceful degradation:
  - If sentence-transformers is not installed, falls back to a hybrid
    Jaccard + SequenceMatcher approach (no ML, but functional).
  - All public methods always return a valid numeric result.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import List

try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BGE retrieval instruction prefix
# Applied to QUERY text only (the new item being matched against corpus)
# ---------------------------------------------------------------------------
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# ---------------------------------------------------------------------------
# Stop-words for the lightweight fallback tokeniser
# ---------------------------------------------------------------------------
_STOP_WORDS = frozenset({
    "i", "my", "a", "an", "the", "and", "or", "in", "on", "at", "to",
    "of", "it", "its", "this", "that", "was", "is", "are", "lost",
    "found", "near", "by", "with", "have", "has", "had", "some", "for",
    "from", "as", "but", "not", "so", "if", "up", "be", "no", "do",
    "we", "he", "she", "they", "our", "their", "his", "her",
})

# Indian campus item vocabulary normalisation
# Maps colloquial / Telugu-English hybrid terms to standard equivalents
# so BGE embeddings are anchored to common vocabulary
_ALIASES: dict[str, str] = {
    # Audio
    "airpods": "wireless earbuds",
    "earphones": "earbuds",
    "headset": "headphones",
    "buds": "earbuds",
    # Eyewear
    "spectacles": "glasses",
    "specs": "glasses",
    "goggles": "glasses",
    # Footwear
    "chappals": "sandals",
    "slippers": "sandals",
    "hawai chappals": "sandals",
    # Phone
    "mobile": "phone",
    "cellphone": "phone",
    "smartphone": "phone",
    # Storage
    "powerbank": "power bank",
    "pen drive": "usb drive",
    "pendrive": "usb drive",
    "flash drive": "usb drive",
    # Identity
    "id card": "identity card",
    "student id": "identity card",
    "college id": "identity card",
    "aadhar": "aadhaar card",
    # Bags
    "bag pack": "backpack",
    "back pack": "backpack",
    "side bag": "sling bag",
    "jhola": "cloth bag",
    # Misc
    "calc": "calculator",
    "water bottle": "bottle",
    "tiffin": "lunch box",
    "tiffin box": "lunch box",
    "xerox": "photocopy",
    "laptop bag": "laptop backpack",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation noise."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _apply_aliases(text: str) -> str:
    """Replace colloquial aliases with standard vocabulary."""
    text = _clean(text)
    for alias, canonical in _ALIASES.items():
        text = re.sub(r"\b" + re.escape(alias) + r"\b", canonical, text)
    return text


def _tokenise(text: str) -> list[str]:
    return [t for t in _clean(text).split() if t not in _STOP_WORDS and len(t) > 1]


def _jaccard_similarity(a: str, b: str) -> float:
    ta, tb = set(_tokenise(a)), set(_tokenise(b))
    if not ta or not tb:
        return 0.0
    intersection = len(ta & tb)
    union = len(ta | tb)
    return intersection / union if union else 0.0


def _seq_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _clean(a), _clean(b)).ratio()


def _fallback_similarity(text1: str, text2: str) -> float:
    """Hybrid: 50% SequenceMatcher + 50% Jaccard (no ML required)."""
    return round(_seq_similarity(text1, text2) * 0.5
                 + _jaccard_similarity(text1, text2) * 0.5, 4)


# ---------------------------------------------------------------------------
# Main Class — BGE Embedder
# ---------------------------------------------------------------------------

class BGEEmbedder:
    """
    BAAI/bge-small-en-v1.5 text embedder for semantic similarity search.

    Key difference from plain SBERT:
      - Uses an instruction prefix for QUERY encoding (retrieval mode)
      - Document corpus is encoded WITHOUT the prefix
      - This asymmetry is what gives BGE its retrieval accuracy advantage

    Usage:
        embedder = BGEEmbedder()
        score = embedder.similarity(
            "Black ASUS laptop with stickers",          # query (lost item)
            "Dark ASUS laptop multiple stickers keyboard damage",  # corpus (found item)
        )
        # → 0.88  (high — BGE understands the paraphrase relationship)
    """

    _MODEL_NAME = "BAAI/bge-small-en-v1.5"
    _FALLBACK_MODEL = "all-MiniLM-L6-v2"   # used if BGE download fails

    def __init__(self):
        self._model = None
        self._available: bool | None = None
        self._using_fallback_model = False
        self.dim = 384

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            try:
                self._model = SentenceTransformer(self._MODEL_NAME)
                logger.info(f"[BGE] Loaded primary model: {self._MODEL_NAME}")
            except Exception:
                # BGE download failed → fallback to MiniLM (already cached likely)
                logger.warning(
                    f"[BGE] Could not load {self._MODEL_NAME}, "
                    f"falling back to {self._FALLBACK_MODEL}"
                )
                self._model = SentenceTransformer(self._FALLBACK_MODEL)
                self._using_fallback_model = True
                logger.info(f"[BGE] Using fallback model: {self._FALLBACK_MODEL}")
            self._available = True
        except Exception as exc:
            self._available = False
            logger.warning(
                f"[BGE] sentence-transformers not available ({exc}). "
                "Using Jaccard+SequenceMatcher fallback."
            )

        return self._available

    def _add_prefix(self, text: str) -> str:
        """Add BGE query instruction prefix (only when using BGE, not MiniLM fallback)."""
        if self._using_fallback_model:
            return text
        return BGE_QUERY_PREFIX + text

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encode(self, text: str, is_query: bool = False) -> np.ndarray:
        """
        Encode a single text into a 384-dim float32 embedding.

        Args:
            text:     Raw text (item name, description, etc.)
            is_query: If True, adds BGE retrieval instruction prefix.
                      Set True for the NEW item being matched.
                      Set False for INDEXED/corpus items.

        Returns:
            np.ndarray of shape (384,), dtype float32.
        """
        text = _apply_aliases(text)
        if not text.strip():
            return np.zeros(self.dim, dtype=np.float32)

        if not self._ensure_loaded() or self._model is None:
            return np.zeros(self.dim, dtype=np.float32)

        if is_query:
            text = self._add_prefix(text)

        try:
            emb = self._model.encode(
                text, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True
            )
            return emb.astype(np.float32)
        except Exception as exc:
            logger.error(f"[BGE] encode failed: {exc}")
            return np.zeros(self.dim, dtype=np.float32)

    def batch_encode(
        self,
        texts: List[str],
        is_query: bool = False,
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Encode multiple texts in a single forward pass.

        Args:
            texts:    List of raw text strings.
            is_query: Apply BGE prefix to all texts if True.
            batch_size: Mini-batch size for encoding.

        Returns:
            np.ndarray of shape (N, 384), dtype float32.
        """
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)

        texts = [_apply_aliases(t) for t in texts]

        if not self._ensure_loaded() or self._model is None:
            return np.zeros((len(texts), self.dim), dtype=np.float32)

        if is_query:
            texts = [self._add_prefix(t) for t in texts]

        try:
            embs = self._model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=batch_size,
                normalize_embeddings=True,
            )
            return embs.astype(np.float32)
        except Exception as exc:
            logger.error(f"[BGE] batch_encode failed: {exc}")
            return np.zeros((len(texts), self.dim), dtype=np.float32)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Cosine similarity between two embeddings.
        BGE encodes with normalize_embeddings=True so this reduces to a dot product.
        """
        n1, n2 = np.linalg.norm(vec1), np.linalg.norm(vec2)
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return float(max(0.0, min(1.0, np.dot(vec1, vec2) / (n1 * n2))))

    def similarity(self, query_text: str, corpus_text: str) -> float:
        """
        Compute semantic similarity between a query and corpus text.

        The query gets the BGE retrieval instruction prefix automatically.
        Corpus text is encoded without prefix.

        Returns:
            float in [0.0, 1.0]. Returns fallback similarity if model unavailable.
        """
        if not query_text or not corpus_text:
            return 0.5  # neutral: insufficient data

        if not self._ensure_loaded():
            return _fallback_similarity(query_text, corpus_text)

        q_emb = self.encode(query_text, is_query=True)
        c_emb = self.encode(corpus_text, is_query=False)
        return self.cosine_similarity(q_emb, c_emb)

    def is_available(self) -> bool:
        return self._ensure_loaded()

    def using_fallback(self) -> bool:
        """Returns True if BGE download failed and MiniLM is being used instead."""
        return self._using_fallback_model

    # ------------------------------------------------------------------
    # Structured text builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_query_text(item: dict, role: str = "lost") -> str:
        """
        Build a rich, structured text representation from item fields.
        Order matters: most discriminative features first.

        Args:
            item: dict from LostItem.to_dict() or FoundItem.to_dict()
            role: "lost" | "found"

        Returns:
            Concatenated string suitable for BGE encoding.
        """
        parts: list[str] = []

        # 1. Category (broadest identifier)
        category = (item.get("category") or "").strip()
        if category:
            parts.append(category)

        # 2. Item name (most specific identifier)
        name = (item.get("item_name") or "").strip()
        if name:
            parts.append(name)

        # 3. Brand + model (exact identifiers — highest discriminative value)
        ad = item.get("additional_details") or {}
        brand = (ad.get("brand") or "").strip()
        model = (ad.get("model") or "").strip()
        if brand:
            parts.append(brand)
        if model:
            parts.append(model)

        # 4. Colour
        colour = (item.get("color") or "").strip()
        if colour:
            parts.append(f"{colour} colour")

        # 5. Unique features from additional details
        for key in ("unique_features", "serial_number", "distinguishing_marks",
                    "size", "material", "pattern"):
            val = (ad.get(key) or "").strip()
            if val:
                parts.append(val)

        # 6. Free-text description (most semantic content)
        desc = (item.get("description") or "").strip()
        if desc:
            parts.append(desc)

        # 7. Location context
        location = (item.get("location") or "").strip()
        if location:
            loc_str = f"found at {location}" if role == "found" else f"lost at {location}"
            parts.append(loc_str)

        return " ".join(parts).strip()


# ---------------------------------------------------------------------------
# Module-level singleton
# Keep old name for backward compatibility with matching_service.py
# ---------------------------------------------------------------------------
bge_embedder = BGEEmbedder()

# Backward-compatible alias — any code importing sbert_embedder still works
sbert_embedder = bge_embedder
