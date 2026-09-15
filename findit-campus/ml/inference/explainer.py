"""
FindIt Campus — Match Explanation Generator
Converts numeric component scores into human-readable match explanations.

WHY EXPLAINABILITY MATTERS:
  A match score of "87%" means nothing to a student.
  "87% match because: ✓ Same ASUS brand, ✓ Similar keyboard damage,
   ✓ Same dark colour, ⚠ Found in nearby location" is actionable.

This module is purely rule-based (no ML). It maps signal strengths
to natural language bullets using threshold bands. Zero latency,
zero dependencies.

Output format:
  {
    "score": 87.0,
    "verdict": "Strong Match",
    "bullets": [
      {"icon": "✅", "text": "Same item category (Laptop)", "signal": "category"},
      {"icon": "✅", "text": "Highly similar description (89% similarity)", "signal": "description"},
      ...
    ],
    "summary": "This item is a strong match (87%) based on matching brand, similar description, and colour.",
    "formatted": "POSSIBLE MATCH: 87%\n\n✅ Same item category (Laptop)\n..."
  }
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Threshold bands for human-readable strength labels
# ---------------------------------------------------------------------------
_SCORE_VERDICT = [
    (95.0, "Excellent Match 🎯"),
    (85.0, "Strong Match ✅"),
    (70.0, "Good Match 🔍"),
    (55.0, "Possible Match ⚠️"),
    (0.0,  "Weak Match ❌"),
]

_SIG_HIGH   = 0.85
_SIG_MED    = 0.65
_SIG_LOW    = 0.40

_IMG_HIGH   = 0.80
_IMG_MED    = 0.60
_IMG_LOW    = 0.35


def _verdict(score: float) -> str:
    for threshold, label in _SCORE_VERDICT:
        if score >= threshold:
            return label
    return "Weak Match ❌"


def _icon(strength: str) -> str:
    return {"high": "✅", "med": "⚠️", "low": "❌", "neutral": "ℹ️"}.get(strength, "ℹ️")


# ---------------------------------------------------------------------------
# Individual signal explainers
# ---------------------------------------------------------------------------

def _explain_description(
    sbert_score: float,
    lost: dict,
    found: dict,
) -> Optional[Dict[str, Any]]:
    """Generate explanation for semantic description similarity."""
    pct = round(sbert_score * 100, 0)

    if sbert_score >= _SIG_HIGH:
        strength, text = "high", f"Highly similar description ({int(pct)}% semantic match)"
    elif sbert_score >= _SIG_MED:
        strength, text = "med", f"Moderately similar description ({int(pct)}% semantic match)"
    elif sbert_score >= _SIG_LOW:
        strength, text = "low", f"Partially similar description ({int(pct)}% semantic match)"
    else:
        strength = "low"
        text = "Descriptions are quite different — other signals drove this match"

    return {
        "icon": _icon(strength),
        "text": text,
        "signal": "description",
        "value": pct,
        "strength": strength,
    }


def _explain_category(lost: dict, found: dict) -> Optional[Dict[str, Any]]:
    """Category match explanation."""
    lc = (lost.get("category") or "").strip().lower()
    fc = (found.get("category") or "").strip().lower()
    if not lc or not fc:
        return None
    if lc == fc:
        return {
            "icon": "✅",
            "text": f"Same item category ({lc.title()})",
            "signal": "category",
            "strength": "high",
        }
    return None  # Category mismatch should never happen (DB pre-filtered)


def _explain_colour(
    color_score: float,
    lost: dict,
    found: dict,
) -> Optional[Dict[str, Any]]:
    lc = (lost.get("color") or "").strip()
    fc = (found.get("color") or "").strip()

    if not lc or not fc:
        return {
            "icon": "ℹ️",
            "text": "Colour not specified by one or both users",
            "signal": "color",
            "strength": "neutral",
        }

    if color_score >= 0.95:
        return {
            "icon": "✅",
            "text": f"Matching colour ({lc} ↔ {fc})",
            "signal": "color",
            "strength": "high",
        }
    elif color_score >= 0.70:
        return {
            "icon": "⚠️",
            "text": f"Similar colour family ({lc} ↔ {fc})",
            "signal": "color",
            "strength": "med",
        }
    elif color_score < 0.40:
        return {
            "icon": "❌",
            "text": f"Colour mismatch ({lc} ↔ {fc})",
            "signal": "color",
            "strength": "low",
        }
    return None


def _explain_brand(
    brand_score: float,
    lost: dict,
    found: dict,
) -> Optional[Dict[str, Any]]:
    lad = lost.get("additional_details") or {}
    fad = found.get("additional_details") or {}
    if not isinstance(lad, dict):
        lad = {}
    if not isinstance(fad, dict):
        fad = {}
    lb = (lost.get("brand") or lad.get("brand") or "").strip()
    fb = (found.get("brand") or fad.get("brand") or "").strip()
    lm = (lost.get("model") or lad.get("model") or "").strip()
    fm = (found.get("model") or fad.get("model") or "").strip()

    if not lb and not fb:
        return None  # No brand info on either side — skip silently

    if lb and fb:
        if lb.lower() == fb.lower():
            brand_line = f"Same {lb} brand confirmed"
            if lm and fm and lm.lower() == fm.lower():
                brand_line += f" ({lm} model)"
            return {"icon": "✅", "text": brand_line, "signal": "brand", "strength": "high"}
        elif lb.lower() in fb.lower() or fb.lower() in lb.lower():
            return {
                "icon": "⚠️",
                "text": f"Partial brand match ({lb} ↔ {fb})",
                "signal": "brand",
                "strength": "med",
            }
        else:
            return {
                "icon": "❌",
                "text": f"Brand mismatch ({lb} ↔ {fb})",
                "signal": "brand",
                "strength": "low",
            }
    elif lb or fb:
        known = lb or fb
        return {
            "icon": "ℹ️",
            "text": f"Brand mentioned: {known} (not confirmed by both users)",
            "signal": "brand",
            "strength": "neutral",
        }
    return None


def _explain_image(
    clip_score: float,
    mode: str,
) -> Optional[Dict[str, Any]]:
    if mode == "text_only":
        return {
            "icon": "ℹ️",
            "text": "No photos uploaded — matched on description only",
            "signal": "image",
            "strength": "neutral",
        }

    pct = round(clip_score * 100, 0)

    if clip_score >= _IMG_HIGH:
        if mode == "both_images":
            text = f"Photos are visually very similar ({int(pct)}% visual match)"
        else:
            text = f"Photo matches description closely ({int(pct)}% cross-modal match)"
        return {"icon": "✅", "text": text, "signal": "image", "strength": "high", "value": pct}

    elif clip_score >= _IMG_MED:
        if mode == "both_images":
            text = f"Photos have moderate visual similarity ({int(pct)}%)"
        else:
            text = f"Photo partially matches description ({int(pct)}%)"
        return {"icon": "⚠️", "text": text, "signal": "image", "strength": "med", "value": pct}

    elif clip_score >= _IMG_LOW:
        text = f"Low visual similarity ({int(pct)}%) — may be different angle or lighting"
        return {"icon": "⚠️", "text": text, "signal": "image", "strength": "low", "value": pct}

    else:
        text = f"Photos appear visually different ({int(pct)}%)"
        return {"icon": "❌", "text": text, "signal": "image", "strength": "low", "value": pct}


def _explain_location(
    location_score: float,
    lost: dict,
    found: dict,
) -> Optional[Dict[str, Any]]:
    ll = (lost.get("location") or "").strip()
    fl = (found.get("location") or "").strip()

    if not ll or not fl:
        return {
            "icon": "ℹ️",
            "text": "Location not specified by one or both users",
            "signal": "location",
            "strength": "neutral",
        }

    if location_score >= 0.95:
        return {"icon": "✅", "text": f"Found at the same location ({fl})", "signal": "location", "strength": "high"}
    elif location_score >= 0.70:
        return {"icon": "⚠️", "text": f"Found in a nearby location (lost: {ll}, found: {fl})", "signal": "location", "strength": "med"}
    elif location_score >= 0.35:
        return {"icon": "⚠️", "text": f"Approximate location match (lost: {ll}, found: {fl})", "signal": "location", "strength": "low"}
    else:
        return {"icon": "❌", "text": f"Different locations (lost: {ll}, found: {fl})", "signal": "location", "strength": "low"}


def _explain_date(
    date_score: float,
    lost: dict,
    found: dict,
) -> Optional[Dict[str, Any]]:
    ld = lost.get("date")
    fd = found.get("date")

    if not ld or not fd:
        return None

    try:
        if hasattr(ld, "strftime"):
            ld_str = ld.strftime("%d %b %Y")
        else:
            from datetime import date
            ld_str = date.fromisoformat(str(ld)).strftime("%d %b %Y")
        if hasattr(fd, "strftime"):
            fd_str = fd.strftime("%d %b %Y")
        else:
            fd_str = date.fromisoformat(str(fd)).strftime("%d %b %Y")
    except Exception:
        ld_str, fd_str = str(ld), str(fd)

    if date_score >= 0.95:
        return {"icon": "✅", "text": f"Found on the same date ({fd_str})", "signal": "date", "strength": "high"}
    elif date_score >= 0.85:
        return {"icon": "✅", "text": f"Found within 1 day (lost: {ld_str}, found: {fd_str})", "signal": "date", "strength": "high"}
    elif date_score >= 0.65:
        return {"icon": "⚠️", "text": f"Found within a few days (lost: {ld_str}, found: {fd_str})", "signal": "date", "strength": "med"}
    elif date_score >= 0.45:
        return {"icon": "⚠️", "text": f"Found within a week (lost: {ld_str}, found: {fd_str})", "signal": "date", "strength": "low"}
    else:
        return {"icon": "❌", "text": f"Large time gap (lost: {ld_str}, found: {fd_str})", "signal": "date", "strength": "low"}


def _explain_blip(blip_used: bool) -> Optional[Dict[str, Any]]:
    if blip_used:
        return {
            "icon": "ℹ️",
            "text": "AI auto-generated description from photo (used for matching)",
            "signal": "blip",
            "strength": "neutral",
        }
    return None


def _explain_unique_features(lost: dict, found: dict) -> Optional[Dict[str, Any]]:
    """Check if unique features are mentioned and match."""
    lad = lost.get("additional_details") or {}
    fad = found.get("additional_details") or {}
    luf = (lad.get("unique_features") or "").strip().lower()
    fuf = (fad.get("unique_features") or "").strip().lower()

    if not luf and not fuf:
        return None

    if luf and fuf:
        # Simple overlap check
        l_tokens = set(luf.split())
        f_tokens = set(fuf.split())
        if len(l_tokens & f_tokens) > 0:
            return {
                "icon": "✅",
                "text": f"Unique features match: \"{luf}\"",
                "signal": "unique_features",
                "strength": "high",
            }
        return {
            "icon": "⚠️",
            "text": f"Unique features described differently ({luf} ↔ {fuf})",
            "signal": "unique_features",
            "strength": "med",
        }
    elif luf:
        return {
            "icon": "ℹ️",
            "text": f"Lost item has unique feature: \"{luf}\"",
            "signal": "unique_features",
            "strength": "neutral",
        }
    return None


# ---------------------------------------------------------------------------
# Main explainer
# ---------------------------------------------------------------------------

class MatchExplainer:
    """
    Converts a scores dict + item dicts into a structured explanation.

    Usage:
        explainer = MatchExplainer()
        explanation = explainer.explain(scores, lost_dict, found_dict)
        print(explanation["formatted"])
        # → "POSSIBLE MATCH: 87%\n\n✅ Same item category..."
    """

    def explain(
        self,
        scores: dict,
        lost: dict,
        found: dict,
    ) -> dict:
        """
        Generate a complete match explanation.

        Args:
            scores: Output from MultimodalMatcher.compute_score()
            lost:   LostItem.to_dict()
            found:  FoundItem.to_dict()

        Returns:
            dict with keys: score, verdict, bullets, summary, formatted, json_str
        """
        overall = scores.get("overall_score", 0.0)
        mode = scores.get("mode", "text_only")
        sbert_raw = scores.get("sbert_score", 0.0) / 100.0
        clip_raw = scores.get("clip_score", 0.0) / 100.0
        color_raw = scores.get("color_score", 0.0) / 100.0
        brand_raw = scores.get("brand_score", 0.0) / 100.0
        location_raw = scores.get("location_score", 0.0) / 100.0
        date_raw = scores.get("date_score", 0.0) / 100.0
        blip_used = scores.get("blip_caption_used", False)

        bullets: List[Dict[str, Any]] = []

        # Order: category → image → description → brand → colour → location → date → special
        cat = _explain_category(lost, found)
        if cat:
            bullets.append(cat)

        img = _explain_image(clip_raw, mode)
        if img:
            bullets.append(img)

        desc = _explain_description(sbert_raw, lost, found)
        if desc:
            bullets.append(desc)

        brand = _explain_brand(brand_raw, lost, found)
        if brand:
            bullets.append(brand)

        uf = _explain_unique_features(lost, found)
        if uf:
            bullets.append(uf)

        col = _explain_colour(color_raw, lost, found)
        if col:
            bullets.append(col)

        loc = _explain_location(location_raw, lost, found)
        if loc:
            bullets.append(loc)

        dt = _explain_date(date_raw, lost, found)
        if dt:
            bullets.append(dt)

        blip = _explain_blip(blip_used)
        if blip:
            bullets.append(blip)

        verdict = _verdict(overall)

        # Build summary sentence
        high_signals = [b["signal"] for b in bullets if b.get("strength") == "high"]
        if high_signals:
            sig_str = ", ".join(s.replace("_", " ") for s in high_signals[:3])
            summary = (
                f"This item is a {verdict.split()[0].lower()} match ({overall:.0f}%) "
                f"based on: {sig_str}."
            )
        else:
            summary = f"This item scored {overall:.0f}% overall. Review details carefully."

        # Formatted string for notifications / UI
        lines = [f"POSSIBLE MATCH: {overall:.0f}%  —  {verdict}", ""]
        for b in bullets:
            lines.append(f"{b['icon']} {b['text']}")

        formatted = "\n".join(lines)

        explanation = {
            "score": overall,
            "verdict": verdict,
            "bullets": bullets,
            "summary": summary,
            "formatted": formatted,
            "json_str": json.dumps(bullets, ensure_ascii=False),
        }

        logger.debug(f"[Explainer] Generated {len(bullets)} bullets for {overall:.0f}% match")
        return explanation


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
match_explainer = MatchExplainer()
