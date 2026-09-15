"""
FindIt Campus — BM25 Keyword Pre-Filter
Stage 2 of the matching pipeline (after DB category filter, before BGE).

WHY BM25:
  BM25 (Best Match 25) is the gold-standard keyword retrieval algorithm.
  It excels where dense neural embeddings struggle:
    - Exact brand/model names: "ASUS ROG Zephyrus" matches exactly
    - Serial numbers or unique codes: "SN: 4XY2201"
    - Rare proper nouns: "Wildcraft Urbane 30L"
  Dense embeddings encode semantics well but can miss exact keyword hits.
  Hybrid BM25 + BGE catches BOTH exact and semantic matches.

  Research shows hybrid retrieval (BM25 + dense) improves recall by 15–25%
  over dense-only retrieval for product/item search tasks.

Reciprocal Rank Fusion (RRF):
  Merges BM25 rankings + BGE cosine rankings without needing score normalisation.
  For each candidate:
    rrf_score = 1/(k + rank_bm25) + 1/(k + rank_bge)
  where k=60 (standard constant).

Pure Python — no GPU, no ML model. Works on Vercel serverless.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# RRF constant (60 is standard, larger k → smoother ranking)
_RRF_K = 60

# Stop-words excluded from BM25 tokenisation
_BM25_STOP = frozenset({
    "i", "a", "an", "the", "and", "or", "in", "on", "at", "to", "of",
    "it", "is", "was", "with", "for", "from", "my", "lost", "found",
    "near", "by", "its", "some", "this", "that", "these", "those",
})


def _tokenise_for_bm25(text: str) -> List[str]:
    """
    Tokenise text for BM25 indexing.
    Preserves brand names, numbers, and abbreviations.
    """
    if not text:
        return []
    text = text.lower()
    # Keep alphanumeric + hyphens (for model names like "S23", "ROG-G15")
    tokens = re.split(r"[^\w\-]+", text)
    return [t for t in tokens if t and t not in _BM25_STOP and len(t) > 1]


def _build_item_document(item: dict) -> str:
    """
    Build a flat BM25-indexable document from item fields.
    Repeats high-importance fields for term frequency weighting.
    """
    parts: List[str] = []
    ad = item.get("additional_details") or {}

    # Repeat brand/model 3× for term frequency boost (BM25 is TF-aware)
    brand = (ad.get("brand") or "").strip()
    model = (ad.get("model") or "").strip()
    if brand:
        parts.extend([brand, brand, brand])
    if model:
        parts.extend([model, model, model])

    # Item name 2×
    name = (item.get("item_name") or "").strip()
    if name:
        parts.extend([name, name])

    # Category 2×
    cat = (item.get("category") or "").strip()
    if cat:
        parts.extend([cat, cat])

    # Colour 1×
    col = (item.get("color") or "").strip()
    if col:
        parts.append(col)

    # Unique features
    for key in ("unique_features", "serial_number", "distinguishing_marks"):
        val = (ad.get(key) or "").strip()
        if val:
            parts.append(val)

    # Description 1×
    desc = (item.get("description") or "").strip()
    if desc:
        parts.append(desc)

    # Location 1×
    loc = (item.get("location") or "").strip()
    if loc:
        parts.append(loc)

    return " ".join(parts)


class BM25Retriever:
    """
    BM25-based keyword pre-filter for candidate item retrieval.

    Provides instant (sub-millisecond) keyword scoring before the
    expensive BGE/SigLIP neural stage runs.

    Usage:
        retriever = BM25Retriever()
        retriever.index(candidates)   # list of item dicts
        top_k = retriever.retrieve(query_item, top_k=20)
        # → [(item_dict, bm25_score), ...]
    """

    def __init__(self):
        self._bm25 = None          # BM25Okapi instance
        self._indexed_items: List[dict] = []
        self._available: Optional[bool] = None
        self._corpus_tokens: List[List[str]] = []

    def _ensure_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from rank_bm25 import BM25Okapi  # type: ignore  # noqa: F401
            self._available = True
            logger.info("[BM25] rank_bm25 available.")
        except ImportError:
            self._available = False
            logger.warning(
                "[BM25] rank_bm25 not installed. "
                "Install with: pip install rank-bm25  "
                "BM25 pre-filter will be skipped (BGE only)."
            )
        return self._available

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index(self, items: List[dict]) -> None:
        """
        Build a BM25 index from a list of candidate item dicts.

        Args:
            items: List of LostItem.to_dict() or FoundItem.to_dict() dicts.
        """
        if not self._ensure_available():
            return

        if not items:
            self._bm25 = None
            self._indexed_items = []
            return

        self._indexed_items = items
        self._corpus_tokens = [
            _tokenise_for_bm25(_build_item_document(item))
            for item in items
        ]

        try:
            from rank_bm25 import BM25Okapi  # type: ignore
            self._bm25 = BM25Okapi(self._corpus_tokens)
            logger.debug(f"[BM25] Indexed {len(items)} candidates.")
        except Exception as exc:
            logger.error(f"[BM25] Indexing failed: {exc}")
            self._bm25 = None

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query_item: dict,
        top_k: int = 20,
    ) -> List[Tuple[dict, float]]:
        """
        Rank candidates by BM25 score against the query item.

        Args:
            query_item: The new lost/found item being matched.
            top_k:      Maximum candidates to return.

        Returns:
            List of (item_dict, bm25_score) sorted descending.
            Returns all items unsorted if BM25 unavailable.
        """
        if not self._ensure_available() or self._bm25 is None:
            # BM25 unavailable → return all candidates with equal score
            return [(item, 1.0) for item in self._indexed_items]

        query_doc = _build_item_document(query_item)
        query_tokens = _tokenise_for_bm25(query_doc)

        if not query_tokens:
            return [(item, 0.0) for item in self._indexed_items]

        try:
            scores = self._bm25.get_scores(query_tokens)
            ranked = sorted(
                zip(self._indexed_items, scores),
                key=lambda x: x[1],
                reverse=True,
            )
            return ranked[:top_k]
        except Exception as exc:
            logger.error(f"[BM25] Retrieval failed: {exc}")
            return [(item, 0.0) for item in self._indexed_items[:top_k]]

    def get_scores(self, query_item: dict) -> Dict[int, float]:
        """
        Return a dict of {report_id → bm25_score} for RRF fusion.
        """
        if not self._ensure_available() or self._bm25 is None:
            return {}

        query_tokens = _tokenise_for_bm25(_build_item_document(query_item))
        if not query_tokens:
            return {}

        try:
            scores = self._bm25.get_scores(query_tokens)
            result = {}
            for item, score in zip(self._indexed_items, scores):
                rid = item.get("report_id")
                if rid is not None:
                    result[rid] = float(score)
            return result
        except Exception as exc:
            logger.error(f"[BM25] get_scores failed: {exc}")
            return {}

    def is_available(self) -> bool:
        return self._ensure_available()


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(
    bm25_scores: Dict[int, float],
    dense_scores: Dict[int, float],
    bm25_weight: float = 0.4,
    dense_weight: float = 0.6,
    k: int = _RRF_K,
) -> List[Tuple[int, float]]:
    """
    Merge BM25 and dense (BGE) rankings using Reciprocal Rank Fusion.

    RRF is robust because it uses RANK positions, not raw scores,
    avoiding the need to normalise incompatible score scales.

    Formula: rrf(d) = Σ 1 / (k + rank_i(d))

    Args:
        bm25_scores:   {report_id → bm25_raw_score}
        dense_scores:  {report_id → cosine_similarity}
        bm25_weight:   Weight multiplier for BM25 rank contribution
        dense_weight:  Weight multiplier for dense rank contribution
        k:             RRF smoothing constant (default 60)

    Returns:
        List of (report_id, rrf_score) sorted descending.
    """
    all_ids = set(bm25_scores.keys()) | set(dense_scores.keys())
    if not all_ids:
        return []

    # Build rank lists
    bm25_ranked = sorted(bm25_scores.keys(), key=lambda x: bm25_scores[x], reverse=True)
    dense_ranked = sorted(dense_scores.keys(), key=lambda x: dense_scores[x], reverse=True)

    bm25_rank = {rid: rank + 1 for rank, rid in enumerate(bm25_ranked)}
    dense_rank = {rid: rank + 1 for rank, rid in enumerate(dense_ranked)}

    rrf_scores: Dict[int, float] = {}
    for rid in all_ids:
        bm25_contrib = bm25_weight / (k + bm25_rank.get(rid, len(all_ids) + 1))
        dense_contrib = dense_weight / (k + dense_rank.get(rid, len(all_ids) + 1))
        rrf_scores[rid] = bm25_contrib + dense_contrib

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
bm25_retriever = BM25Retriever()
