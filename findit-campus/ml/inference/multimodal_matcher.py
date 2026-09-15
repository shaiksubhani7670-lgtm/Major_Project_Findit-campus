"""
FindIt Campus — Multimodal Match Scorer  (v3.0 — Expert Architecture)

UPGRADE SUMMARY (v2 → v3):
  • Text model: all-MiniLM-L6-v2 → BAAI/bge-small-en-v1.5 (+10% MTEB)
  • Image model: CLIP ViT-B/32   → Google SigLIP base-patch16-256 (+2-3%)
  • NEW: Match explainability via explainer.py
  • Text-only weight raised to 50% (description is PRIMARY feature)
  • SigLIP image weight raised to 35% in both-image mode (more accurate model)
  • BM25 hybrid retrieval handled upstream in matching_service.py
  • Multi-image scoring: top-3 pair averaging (from v2.1, retained)
  • Dual-signal confirmation boost (from v2.1, retained)

Design rules (unchanged):
  - Image upload is OPTIONAL — text-only mode always works
  - BLIP fires only when image exists but description < 30 chars
  - Found items remain completely private
  - All scores in returned dict map directly to Match model fields
"""

from __future__ import annotations

import logging
import re
from datetime import date as Date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Noise guard — SigLIP/CLIP scores below this are treated as unreliable
# ---------------------------------------------------------------------------
MIN_VISUAL_CONFIDENCE: float = 0.25

# Dual-signal confirmation boost (both BGE AND SigLIP agree ≥ threshold)
CONFIRM_THRESHOLD: float = 0.65
CONFIRM_BOOST: float = 3.5   # percentage points

# ---------------------------------------------------------------------------
# Adaptive scoring weights — THREE regimes
# ---------------------------------------------------------------------------

# TEXT-ONLY (no images on either side) — description is PRIMARY
# BGE weight raised from 45% → 50% because BGE is more accurate
_WEIGHTS_TEXT_ONLY: Dict[str, float] = {
    "text":     0.50,   # BGE semantic description
    "visual":   0.00,   # N/A
    "color":    0.15,
    "brand":    0.20,
    "location": 0.10,
    "date":     0.05,
}

# BOTH IMAGES — visual signal is strong, text remains important
# SigLIP weight raised from 30% → 35% (more accurate model)
_WEIGHTS_BOTH_IMAGES: Dict[str, float] = {
    "text":     0.25,
    "visual":   0.35,   # SigLIP image↔image
    "color":    0.10,
    "brand":    0.10,
    "location": 0.12,
    "date":     0.08,
}

# ONE IMAGE — cross-modal text↔image
_WEIGHTS_ONE_IMAGE: Dict[str, float] = {
    "text":     0.30,
    "visual":   0.22,   # SigLIP text↔image cross-modal
    "color":    0.15,
    "brand":    0.15,
    "location": 0.13,
    "date":     0.05,
}

# ---------------------------------------------------------------------------
# Colour groupings for soft matching
# ---------------------------------------------------------------------------
_COLOR_GROUPS: Dict[str, List[str]] = {
    "blue":   ["dark blue", "navy", "navy blue", "sky blue", "light blue", "cobalt", "denim"],
    "black":  ["grey", "dark grey", "charcoal", "graphite", "dark gray", "matte black"],
    "white":  ["cream", "silver", "off white", "ivory", "light grey", "light gray", "pearl"],
    "red":    ["maroon", "pink", "rose", "dark red", "crimson", "burgundy"],
    "green":  ["dark green", "olive", "lime", "forest green", "mint", "teal"],
    "yellow": ["gold", "mustard", "amber", "orange", "saffron"],
    "brown":  ["tan", "beige", "khaki", "coffee", "chocolate", "caramel"],
    "purple": ["violet", "lavender", "indigo", "magenta"],
}


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _colour_score(lost_colour: str, found_colour: str) -> float:
    lc = (lost_colour or "").strip().lower()
    fc = (found_colour or "").strip().lower()

    if not lc or not fc:
        return 0.5   # neutral: unknown

    if lc == fc:
        return 1.0

    if lc in fc or fc in lc:
        return 0.85

    for base, variants in _COLOR_GROUPS.items():
        group = {base} | set(variants)
        if lc in group and fc in group:
            return 0.70

    return 0.0


def _brand_score(lost_ad: Optional[dict], found_ad: Optional[dict]) -> float:
    ld, fd = (lost_ad or {}), (found_ad or {})

    lb = (ld.get("brand") or "").strip().lower()
    fb = (fd.get("brand") or "").strip().lower()
    lm = (ld.get("model") or "").strip().lower()
    fm = (fd.get("model") or "").strip().lower()

    if not lb and not fb:
        return 0.5   # no brand info — neutral

    if lb and fb:
        if lb == fb:
            brand_sim = 1.0
        elif lb in fb or fb in lb:
            brand_sim = 0.8
        else:
            brand_sim = 0.0
    else:
        brand_sim = 0.5   # one side unknown

    if lm and fm:
        if lm == fm:
            model_sim = 1.0
        elif lm in fm or fm in lm:
            model_sim = 0.8
        else:
            model_sim = 0.0
    else:
        model_sim = 0.5

    return brand_sim * 0.6 + model_sim * 0.4


def _location_score(lost_loc: str, found_loc: str) -> float:
    ll = (lost_loc or "").strip().lower()
    fl = (found_loc or "").strip().lower()

    if not ll or not fl:
        return 0.5

    if ll == fl:
        return 1.0

    ll_tokens = set(re.split(r"[\s,./\-]+", ll)) - {"", "and", "or", "at", "near", "the"}
    fl_tokens = set(re.split(r"[\s,./\-]+", fl)) - {"", "and", "or", "at", "near", "the"}

    if ll_tokens and fl_tokens:
        overlap = len(ll_tokens & fl_tokens) / max(len(ll_tokens), len(fl_tokens))
        if overlap >= 0.5:
            return 0.8
        if overlap > 0:
            return 0.4

    return 0.1


def _date_score(lost_date: Any, found_date: Any) -> float:
    if not lost_date or not found_date:
        return 0.5

    try:
        if isinstance(lost_date, str):
            lost_date = Date.fromisoformat(lost_date)
        if isinstance(found_date, str):
            found_date = Date.fromisoformat(found_date)
        diff = abs((found_date - lost_date).days)
    except Exception:
        return 0.5

    if diff == 0:     return 1.0
    if diff <= 1:     return 0.90
    if diff <= 3:     return 0.70
    if diff <= 7:     return 0.50
    if diff <= 14:    return 0.30
    if diff <= 30:    return 0.10
    return 0.0


# ---------------------------------------------------------------------------
# Multi-image SigLIP helpers (findit_ml majority_label pattern)
# ---------------------------------------------------------------------------

def _get_all_images(item: dict) -> List[str]:
    """Collect all usable image URLs from an item (up to 5)."""
    urls: List[str] = []
    for url in (item.get("image_paths") or []):
        url = (url or "").strip()
        if url and url not in urls:
            urls.append(url)
    single = (item.get("image_path") or "").strip()
    if single and single not in urls:
        urls.insert(0, single)
    return urls[:5]


def _multi_image_score(
    lost_images: List[str],
    found_images: List[str],
    visual_matcher,
) -> float:
    """
    Average SigLIP score across all image pair combinations.
    Uses top-3 pairs to avoid one lucky match dominating.
    Noise guard: excludes pairs below MIN_VISUAL_CONFIDENCE.
    """
    if not lost_images or not found_images:
        return 0.5

    pair_scores: List[float] = []
    for li in lost_images:
        for fi in found_images:
            try:
                s = visual_matcher.image_image_similarity(li, fi)
                if s >= MIN_VISUAL_CONFIDENCE:
                    pair_scores.append(s)
            except Exception:
                pass

    if not pair_scores:
        return 0.5

    top3 = sorted(pair_scores, reverse=True)[:3]
    return float(sum(top3) / len(top3))


def _cross_modal_score(
    text: str,
    images: List[str],
    visual_matcher,
) -> float:
    """Average SigLIP text↔image score across all images above noise threshold."""
    if not text or not images:
        return 0.5

    scores: List[float] = []
    for img in images:
        try:
            s = visual_matcher.text_image_similarity(text, img)
            if s >= MIN_VISUAL_CONFIDENCE:
                scores.append(s)
        except Exception:
            pass

    return float(sum(scores) / len(scores)) if scores else 0.5


def _dual_signal_boost(text_sim: float, visual_sim: float, overall: float) -> float:
    """Apply +3.5pt boost when both BGE AND SigLIP independently confirm the match."""
    if text_sim >= CONFIRM_THRESHOLD and visual_sim >= CONFIRM_THRESHOLD:
        return min(100.0, overall + CONFIRM_BOOST)
    return overall


# ---------------------------------------------------------------------------
# Main Multimodal Matcher
# ---------------------------------------------------------------------------

class MultimodalMatcher:
    """
    Unified multimodal scoring engine (Expert v3.0).

    Orchestrates:
      1. BLIP caption enrichment (when image exists, description is sparse)
      2. BGE-small-en-v1.5 semantic text similarity (PRIMARY)
      3. SigLIP cross-modal image/text matching (WHEN IMAGES AVAILABLE)
      4. Colour / Brand / Location / Date heuristic signals
      5. Adaptive weight fusion
      6. Dual-signal confirmation boost
      7. Match explanation generation

    Usage:
        result = multimodal_matcher.compute_score(lost.to_dict(), found.to_dict())
        result["overall_score"]  # 0–100
        result["explanation"]["formatted"]  # human-readable bullets
    """

    def __init__(self):
        self._bge = None
        self._siglip = None
        self._blip = None
        self._explainer = None

    def _get_bge(self):
        if self._bge is None:
            from ml.inference.sbert_embedder import bge_embedder
            self._bge = bge_embedder
        return self._bge

    def _get_siglip(self):
        if self._siglip is None:
            from ml.inference.clip_matcher import siglip_matcher
            self._siglip = siglip_matcher
        return self._siglip

    def _get_blip(self):
        if self._blip is None:
            from ml.inference.blip_captioner import blip_captioner
            self._blip = blip_captioner
        return self._blip

    def _get_explainer(self):
        if self._explainer is None:
            from ml.inference.explainer import match_explainer
            self._explainer = match_explainer
        return self._explainer

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------

    def compute_score(self, lost: dict, found: dict) -> dict:
        """
        Compute the full multimodal match score between a lost and found item.

        Returns:
            dict with keys matching Match model + explanation:
              overall_score      float  0–100
              text_score         float  0–100  (BGE)
              visual_score       float  0–100  (SigLIP)
              sbert_score        float  0–100  (alias for text_score)
              clip_score         float  0–100  (alias for visual_score)
              image_score        float  0–100  (DB compat alias)
              description_score  float  0–100  (DB compat alias)
              brand_score        float  0–100
              color_score        float  0–100
              location_score     float  0–100
              date_score         float  0–100
              question_score     float  50.0   (set by matching_service QA)
              blip_caption_used  bool
              mode               str   text_only | both_images | one_image
              explanation        dict  (human-readable match explanation)
        """
        # ----------------------------------------------------------------
        # 1. Collect ALL images (up to 5 per item)
        # ----------------------------------------------------------------
        lost_images = _get_all_images(lost)
        found_images = _get_all_images(found)

        lost_img  = lost_images[0]  if lost_images  else None
        found_img = found_images[0] if found_images else None

        both_images = bool(lost_images and found_images)
        one_image   = bool(lost_images or found_images) and not both_images

        if both_images:
            weights, mode = _WEIGHTS_BOTH_IMAGES, "both_images"
        elif one_image:
            weights, mode = _WEIGHTS_ONE_IMAGE, "one_image"
        else:
            weights, mode = _WEIGHTS_TEXT_ONLY, "text_only"

        # ----------------------------------------------------------------
        # 2. BLIP — enrich sparse descriptions from images
        # ----------------------------------------------------------------
        blip_used = False
        blip = self._get_blip()

        lost_desc  = (lost.get("description")  or "")
        found_desc = (found.get("description") or "")

        if lost_img and blip.is_available():
            lost_desc, used  = blip.enrich_description(lost_desc, lost_img)
            blip_used = blip_used or used

        if found_img and blip.is_available():
            found_desc, used = blip.enrich_description(found_desc, found_img)
            blip_used = blip_used or used

        lost_enriched  = {**lost,  "description": lost_desc}
        found_enriched = {**found, "description": found_desc}

        # ----------------------------------------------------------------
        # 3. BGE text similarity (PRIMARY SIGNAL)
        #    Uses instruction prefix for query encoding — key BGE advantage
        # ----------------------------------------------------------------
        bge = self._get_bge()
        lost_text  = bge.build_query_text(lost_enriched,  role="lost")
        found_text = bge.build_query_text(found_enriched, role="found")
        text_sim = bge.similarity(lost_text, found_text)

        # ----------------------------------------------------------------
        # 4. SigLIP visual / cross-modal similarity
        # ----------------------------------------------------------------
        visual_sim = 0.0
        siglip = self._get_siglip()

        if both_images and siglip.is_available():
            # Multi-image averaging across all uploaded photos
            visual_sim = _multi_image_score(lost_images, found_images, siglip)
        elif one_image and siglip.is_available():
            if lost_images:
                # Found has only text → found_text ↔ lost images
                visual_sim = _cross_modal_score(found_text, lost_images, siglip)
            else:
                # Lost has only text → lost_text ↔ found images
                visual_sim = _cross_modal_score(lost_text, found_images, siglip)

        # ----------------------------------------------------------------
        # 5. Heuristic signals
        # ----------------------------------------------------------------
        col_sim  = _colour_score(
            lost.get("color", ""), found.get("color", "")
        )
        brand_sim = _brand_score(
            lost.get("additional_details"),
            found.get("additional_details"),
        )
        loc_sim  = _location_score(
            lost.get("location", ""), found.get("location", "")
        )
        date_sim = _date_score(
            lost.get("date"), found.get("date")
        )

        # ----------------------------------------------------------------
        # 6. Weighted aggregation
        # ----------------------------------------------------------------
        raw = {
            "text":     text_sim,
            "visual":   visual_sim,
            "color":    col_sim,
            "brand":    brand_sim,
            "location": loc_sim,
            "date":     date_sim,
        }
        overall = sum(raw[k] * weights[k] for k in weights) * 100.0

        # 6a. Dual-signal confirmation boost
        if both_images or one_image:
            overall = _dual_signal_boost(text_sim, visual_sim, overall)

        # 6b. Structural perfect-match boost
        if col_sim >= 0.95 and brand_sim >= 0.95 and loc_sim >= 0.95 and date_sim >= 0.90:
            overall = max(overall, 96.5)

        overall = round(overall, 1)

        # ----------------------------------------------------------------
        # 7. Build result dict
        # ----------------------------------------------------------------
        result = {
            # Core scores (DB-compatible field names)
            "overall_score":      overall,
            "description_score":  round(text_sim  * 100, 1),
            "image_score":        round(visual_sim * 100, 1),
            "brand_score":        round(brand_sim  * 100, 1),
            "color_score":        round(col_sim    * 100, 1),
            "location_score":     round(loc_sim    * 100, 1),
            "question_score":     50.0,           # placeholder — set by service QA logic
            # New v3 scores
            "text_score":         round(text_sim   * 100, 1),
            "visual_score":       round(visual_sim * 100, 1),
            "date_score":         round(date_sim   * 100, 1),
            # Backward-compat aliases
            "sbert_score":        round(text_sim   * 100, 1),
            "clip_score":         round(visual_sim * 100, 1),
            # Metadata
            "blip_caption_used":  blip_used,
            "mode":               mode,
            "n_lost_images":      len(lost_images),
            "n_found_images":     len(found_images),
            "raw_signals":        raw,
        }

        # ----------------------------------------------------------------
        # 8. Generate human-readable explanation
        # ----------------------------------------------------------------
        try:
            explainer = self._get_explainer()
            explanation = explainer.explain(result, lost, found)
            result["explanation"] = explanation
        except Exception as exc:
            logger.warning(f"[Matcher] Explainer failed: {exc}")
            result["explanation"] = {
                "score": overall,
                "verdict": "Match",
                "bullets": [],
                "summary": f"Match score: {overall:.0f}%",
                "formatted": f"POSSIBLE MATCH: {overall:.0f}%",
                "json_str": "[]",
            }

        logger.info(
            f"[Matcher] Lost#{lost.get('report_id')} ↔ Found#{found.get('report_id')} | "
            f"Mode={mode} | Imgs={len(lost_images)}L×{len(found_images)}F | "
            f"BGE={text_sim:.3f} | SigLIP={visual_sim:.3f} | "
            f"Color={col_sim:.3f} | Brand={brand_sim:.3f} | "
            f"Loc={loc_sim:.3f} | Date={date_sim:.3f} → {overall}%"
        )

        return result

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def is_bge_available(self) -> bool:
        return self._get_bge().is_available()

    def is_siglip_available(self) -> bool:
        return self._get_siglip().is_available()

    def is_blip_available(self) -> bool:
        return self._get_blip().is_available()

    # Backward-compat aliases
    def is_sbert_available(self) -> bool:
        return self.is_bge_available()

    def is_clip_available(self) -> bool:
        return self.is_siglip_available()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
multimodal_matcher = MultimodalMatcher()
