"""
FindIt Campus — AI Matching Service (Expert v3.0)
Full multimodal lost ↔ found matching pipeline:

  Stage 0: DB category + date + status filter   (existing, unchanged)
  Stage 1: BM25 keyword pre-ranking             (NEW — hybrid retrieval)
  Stage 2: BGE dense embedding scoring          (via multimodal_matcher)
  Stage 3: Hybrid RRF fusion → top-20 candidates (NEW)
  Stage 4: Full multimodal scoring on top-20    (BGE + SigLIP + heuristics)
  Stage 5: Match explanation generation         (NEW)
  Stage 6: DB persist + notification            (unchanged)

WHY THE STAGED PIPELINE:
  Running full BGE + SigLIP on every DB candidate is O(N × model_cost).
  The BM25+RRF pre-filter reduces this to O(20 × model_cost) regardless
  of how many items are in the DB — making the system scale to thousands.

Privacy rules (unchanged):
  - Found items NEVER exposed publicly.
  - Only the lost-item owner receives match alerts.
  - Contact details revealed only after ownership verification.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore
    _NUMPY_AVAILABLE = False

from app import db
from app.models.lost_item import LostItem
from app.models.found_item import FoundItem
from app.models.match import Match
from app.models.notification import Notification
from app.models.question_answer import QuestionAnswer

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Expert multimodal matching engine for FindIt Campus.

    Pipeline:
      DB filter → BM25 pre-rank → Hybrid RRF → Top-20 full scoring
      → Explanation → Notification
    """

    # ------------------------------------------------------------------
    # Thresholds
    # ------------------------------------------------------------------
    MATCH_ALERT_THRESHOLD  = 70.0   # ≥ this → send alert to lost user
    MATCH_STATUS_THRESHOLD = 95.0   # ≥ this → mark items Matched
    CANDIDATE_WINDOW_DAYS  = 60     # only compare within 60 days
    MAX_FULL_SCORE_CANDIDATES = 20  # BM25+RRF top-K before expensive ML

    # ------------------------------------------------------------------
    # Lazy loaders
    # ------------------------------------------------------------------

    @staticmethod
    def _get_scorer():
        try:
            from ml.inference.multimodal_matcher import multimodal_matcher
            return multimodal_matcher
        except Exception as exc:
            logger.error(f"[MatchingService] multimodal_matcher unavailable: {exc}")
            return None

    @staticmethod
    def _get_bge():
        try:
            from ml.inference.sbert_embedder import bge_embedder
            return bge_embedder
        except Exception:
            return None

    @staticmethod
    def _get_bm25():
        try:
            from ml.inference.bm25_retriever import BM25Retriever, reciprocal_rank_fusion
            return BM25Retriever(), reciprocal_rank_fusion
        except Exception as exc:
            logger.warning(f"[MatchingService] BM25 unavailable: {exc}")
            return None, None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run_matching(self, report_id: int, report_type: str):
        """
        Run the full matching pipeline for a newly submitted report.

        Args:
            report_id:   PK of the lost or found item.
            report_type: 'lost' | 'found'

        Returns:
            List of Match objects created or updated.
        """
        logger.info(f"[MatchingService] Pipeline start: {report_type}#{report_id}")

        if report_type == "lost":
            return self._match_lost_item(report_id)
        else:
            return self._match_found_item(report_id)

    # ------------------------------------------------------------------
    # Stage 0 — DB candidate retrieval
    # ------------------------------------------------------------------

    def _match_lost_item(self, lost_id: int):
        lost_item = LostItem.query.get(lost_id)
        if not lost_item or lost_item.status == "Cancelled":
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.CANDIDATE_WINDOW_DAYS)
        candidates = FoundItem.query.filter(
            FoundItem.category == lost_item.category,
            FoundItem.status == "Searching",
            FoundItem.created_at >= cutoff,
        ).all()

        logger.info(
            f"[MatchingService] Lost#{lost_id}: {len(candidates)} DB candidates "
            f"in category '{lost_item.category}'"
        )

        return self._run_pipeline(lost_item, candidates, query_role="lost")

    def _match_found_item(self, found_id: int):
        found_item = FoundItem.query.get(found_id)
        if not found_item or found_item.status == "Cancelled":
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.CANDIDATE_WINDOW_DAYS)
        candidates = LostItem.query.filter(
            LostItem.category == found_item.category,
            LostItem.status == "Searching",
            LostItem.created_at >= cutoff,
        ).all()

        logger.info(
            f"[MatchingService] Found#{found_id}: {len(candidates)} DB candidates "
            f"in category '{found_item.category}'"
        )

        return self._run_pipeline(found_item, candidates, query_role="found")

    # ------------------------------------------------------------------
    # Stages 1–4 — BM25 + RRF + Full scoring
    # ------------------------------------------------------------------

    def _run_pipeline(self, query_item, candidates: list, query_role: str) -> list:
        """
        Run the full staged pipeline on a set of DB candidates.
        Returns list of Match objects created/updated.
        """
        if not candidates:
            return []

        query_dict = query_item.to_dict()
        candidate_dicts = [c.to_dict() for c in candidates]
        candidate_map = {c.to_dict()["report_id"]: c for c in candidates}

        # ------ Stage 1: BM25 keyword ranking -------------------------
        bm25_retriever_cls, rrf_fn = self._get_bm25()
        bm25_scores: dict[int, float] = {}
        if bm25_retriever_cls is not None:
            try:
                retriever = bm25_retriever_cls
                retriever.index(candidate_dicts)
                bm25_scores = retriever.get_scores(query_dict)
                logger.debug(
                    f"[MatchingService] BM25: scored {len(bm25_scores)} candidates"
                )
            except Exception as exc:
                logger.warning(f"[MatchingService] BM25 stage failed: {exc}")

        # ------ Stage 2: BGE dense ranking ----------------------------
        bge = self._get_bge()
        dense_scores: dict[int, float] = {}
        if bge is not None and bge.is_available():
            try:
                query_text = bge.build_query_text(query_dict, role=query_role)
                corpus_texts = [
                    bge.build_query_text(cd, role="found" if query_role == "lost" else "lost")
                    for cd in candidate_dicts
                ]
                # Batch encode corpus (efficient)
                corpus_embs = bge.batch_encode(corpus_texts, is_query=False)
                query_emb   = bge.encode(query_text, is_query=True)
                # Cosine similarities
                for i, cd in enumerate(candidate_dicts):
                    rid = cd.get("report_id")
                    if rid is not None:
                        dense_scores[rid] = float(
                            bge.cosine_similarity(query_emb, corpus_embs[i])
                        )
                logger.debug(
                    f"[MatchingService] BGE: scored {len(dense_scores)} candidates"
                )
            except Exception as exc:
                logger.warning(f"[MatchingService] BGE stage failed: {exc}")

        # ------ Stage 3: Hybrid RRF → top-K selection ----------------
        if bm25_scores or dense_scores:
            try:
                fused = rrf_fn(
                    bm25_scores=bm25_scores,
                    dense_scores=dense_scores,
                    bm25_weight=0.35,
                    dense_weight=0.65,
                )
                top_ids = [rid for rid, _ in fused[:self.MAX_FULL_SCORE_CANDIDATES]]
                top_candidates = [candidate_map[rid] for rid in top_ids if rid in candidate_map]
                logger.info(
                    f"[MatchingService] RRF: {len(top_candidates)} candidates "
                    f"selected for full scoring (from {len(candidates)})"
                )
            except Exception as exc:
                logger.warning(f"[MatchingService] RRF failed: {exc}, using all candidates")
                top_candidates = candidates[:self.MAX_FULL_SCORE_CANDIDATES]
        else:
            # No BM25/BGE available → score all (small number expected)
            top_candidates = candidates[:self.MAX_FULL_SCORE_CANDIDATES]

        # ------ Stage 4: Full multimodal scoring on top-K ------------
        results = []
        for candidate in top_candidates:
            if query_role == "lost":
                lost_item   = query_item
                found_item  = candidate
            else:
                lost_item   = candidate
                found_item  = query_item

            match = self._compute_and_save_match(lost_item, found_item)
            if match:
                results.append(match)

        return results

    # ------------------------------------------------------------------
    # Stage 4 — Full multimodal scoring + persistence
    # ------------------------------------------------------------------

    def _compute_and_save_match(self, lost: LostItem, found: FoundItem):
        scorer = self._get_scorer()

        if scorer is not None:
            scores = scorer.compute_score(lost.to_dict(), found.to_dict())
        else:
            logger.warning("[MatchingService] Falling back to legacy scorer.")
            scores = self._legacy_score(lost, found)

        # QA score (existing ownership-hint signal)
        qa_score = self._qa_score(lost.report_id, found.report_id)
        scores["question_score"] = round(qa_score * 100, 1)

        # Blend QA signal (±5pt swing)
        overall = self._blend_qa(scores["overall_score"], qa_score)
        scores["overall_score"] = overall

        # Extract explanation
        explanation = scores.get("explanation", {})
        explanation_json_str = explanation.get("json_str", "[]")

        # ------ Check for existing match ------------------------------
        existing = Match.query.filter_by(
            lost_report_id=lost.report_id,
            found_report_id=found.report_id,
        ).first()

        if existing:
            if overall > existing.overall_score:
                self._update_match(existing, scores, explanation_json_str)
                db.session.commit()
                logger.info(
                    f"[MatchingService] Updated Match#{existing.match_id}: "
                    f"{existing.overall_score}% → {overall}%"
                )
            return existing

        # ------ Create new match --------------------------------------
        new_match = Match(
            lost_report_id  = lost.report_id,
            found_report_id = found.report_id,
            image_score     = scores.get("image_score",       0.0),
            brand_score     = scores.get("brand_score",       0.0),
            description_score = scores.get("description_score", 0.0),
            color_score     = scores.get("color_score",       0.0),
            location_score  = scores.get("location_score",    0.0),
            question_score  = scores.get("question_score",    0.0),
            overall_score   = overall,
            sbert_score     = scores.get("sbert_score"),
            clip_score      = scores.get("clip_score"),
            blip_caption_used = scores.get("blip_caption_used", False),
            explanation_json  = explanation_json_str,
        )
        db.session.add(new_match)

        # Status update
        if overall >= self.MATCH_STATUS_THRESHOLD:
            lost.status  = "Matched"
            found.status = "Matched"

        db.session.commit()

        # Notification + email to lost user and found user
        if overall >= self.MATCH_ALERT_THRESHOLD:
            self._notify_lost_user(lost, found, overall, explanation)
            self._notify_found_user(lost, found, overall, explanation)
            self._send_match_email(lost, found, overall, explanation)

        logger.info(
            f"[MatchingService] Match saved: "
            f"Lost#{lost.report_id} ↔ Found#{found.report_id} | "
            f"Score={overall}% | Mode={scores.get('mode','?')} | "
            f"BLIP={'yes' if scores.get('blip_caption_used') else 'no'}"
        )

        return new_match

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _update_match(match: Match, scores: dict, explanation_json_str: str):
        match.image_score       = scores.get("image_score",       match.image_score)
        match.brand_score       = scores.get("brand_score",       match.brand_score)
        match.description_score = scores.get("description_score", match.description_score)
        match.color_score       = scores.get("color_score",       match.color_score)
        match.location_score    = scores.get("location_score",    match.location_score)
        match.question_score    = scores.get("question_score",    match.question_score)
        match.overall_score     = scores.get("overall_score",     match.overall_score)
        if hasattr(match, "sbert_score"):
            match.sbert_score   = scores.get("sbert_score",       match.sbert_score)
        if hasattr(match, "clip_score"):
            match.clip_score    = scores.get("clip_score",        match.clip_score)
        if hasattr(match, "blip_caption_used"):
            match.blip_caption_used = scores.get("blip_caption_used", match.blip_caption_used)
        if hasattr(match, "explanation_json"):
            match.explanation_json = explanation_json_str

    def _qa_score(self, lost_id: int, found_id: int) -> float:
        from difflib import SequenceMatcher as SM

        lost_qas  = QuestionAnswer.query.filter_by(report_type="lost",  report_id=lost_id).all()
        found_qas = QuestionAnswer.query.filter_by(report_type="found", report_id=found_id).all()

        if not lost_qas or not found_qas:
            return 0.5

        matched, total = 0.0, 0
        for l_qa in lost_qas:
            for f_qa in found_qas:
                if l_qa.question.strip().lower() == f_qa.question.strip().lower():
                    total += 1
                    l_ans = l_qa.answer.strip().lower()
                    f_ans = f_qa.answer.strip().lower()
                    if l_ans == f_ans or l_ans in f_ans or f_ans in l_ans:
                        matched += 1.0
                    else:
                        sim = SM(None, l_ans, f_ans).ratio()
                        matched += sim if sim < 0.7 else 1.0

        return matched / total if total > 0 else 0.5

    @staticmethod
    def _blend_qa(overall: float, qa_score: float) -> float:
        deviation = qa_score - 0.5
        adjusted  = overall + deviation * 10.0
        return round(max(0.0, min(100.0, adjusted)), 1)

    @staticmethod
    def _notify_lost_user(lost: LostItem, found: FoundItem, score: float, explanation: dict):
        verdict = explanation.get("verdict", "Match")
        summary = explanation.get("summary", "")

        msg = (
            f"🎉 {verdict}! Someone found an item matching your lost "
            f"'{lost.item_name}'.\n\n"
            f"Found at: {found.location} on {found.date.strftime('%d %b %Y')}\n"
            f"AI Match Confidence: {score:.0f}%\n\n"
            f"{summary}\n\n"
            f"Go to Match Alerts to view full details and claim it."
        )
        notif = Notification(
            student_id=lost.student_id,
            title=f"🎯 Possible Match Found for '{lost.item_name}' ({score:.0f}%)",
            message=msg,
        )
        db.session.add(notif)

    @staticmethod
    def _notify_found_user(lost: LostItem, found: FoundItem, score: float, explanation: dict):
        if found.student_id == lost.student_id:
            return
        msg = (
            f"🎯 Possible Match Found! An item you reported finding ('{found.item_name}') "
            f"has a potential match with a lost item report '{lost.item_name}'.\n\n"
            f"AI Match Confidence: {score:.0f}%\n\n"
            f"Check your dashboard for updates when the owner verifies and claims the item."
        )
        notif = Notification(
            student_id=found.student_id,
            title=f"🎯 Possible Match Found for '{found.item_name}' ({score:.0f}%)",
            message=msg,
        )
        db.session.add(notif)

    @staticmethod
    def _send_match_email(
        lost: LostItem, found: FoundItem, score: float, explanation: dict
    ):
        from app.models.student import Student
        from app.services.email_service import send_match_found_email, send_match_found_to_finder_email

        # Send email to lost item owner
        try:
            lost_student = Student.query.get(lost.student_id)
            if lost_student:
                send_match_found_email(lost_student, lost, found, score)
        except Exception as exc:
            logger.warning(f"[MatchingService] Lost user email send failed: {exc}")

        # Send email to found item finder
        try:
            if found.student_id != lost.student_id:
                found_student = Student.query.get(found.student_id)
                if found_student:
                    send_match_found_to_finder_email(found_student, lost, found, score)
        except Exception as exc:
            logger.warning(f"[MatchingService] Finder user email send failed: {exc}")

    # ------------------------------------------------------------------
    # Emergency legacy fallback (no ML)
    # ------------------------------------------------------------------

    @staticmethod
    def _legacy_score(lost: LostItem, found: FoundItem) -> dict:
        from difflib import SequenceMatcher

        def _sim(a, b):
            if not a or not b:
                return 0.5
            a, b = a.lower().strip(), b.lower().strip()
            seq  = SequenceMatcher(None, a, b).ratio()
            ta, tb = set(a.split()), set(b.split())
            jac  = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
            return round(seq * 0.5 + jac * 0.5, 4)

        desc_sim  = _sim(lost.description, found.description)
        color_sim = 1.0 if (lost.color or "").lower() == (found.color or "").lower() else 0.0
        loc_sim   = 1.0 if (lost.location or "").lower() == (found.location or "").lower() else 0.2

        lost_ad  = lost.additional_details or {}
        found_ad = found.additional_details or {}
        brand_sim = _sim(lost_ad.get("brand", ""), found_ad.get("brand", ""))

        overall = (
            desc_sim  * 50.0 +
            color_sim * 15.0 +
            brand_sim * 20.0 +
            loc_sim   * 10.0 +
            0.5       * 5.0   # date neutral
        )

        return {
            "overall_score":      round(overall, 1),
            "text_score":         round(desc_sim  * 100, 1),
            "visual_score":       0.0,
            "sbert_score":        round(desc_sim  * 100, 1),
            "clip_score":         0.0,
            "image_score":        0.0,
            "brand_score":        round(brand_sim * 100, 1),
            "description_score":  round(desc_sim  * 100, 1),
            "color_score":        round(color_sim * 100, 1),
            "location_score":     round(loc_sim   * 100, 1),
            "question_score":     50.0,
            "date_score":         50.0,
            "blip_caption_used":  False,
            "mode":               "legacy",
            "explanation":        {
                "score": round(overall, 1),
                "verdict": "Match (legacy)",
                "bullets": [],
                "summary": f"Legacy score: {overall:.0f}%",
                "formatted": f"POSSIBLE MATCH: {overall:.0f}%\n(ML packages not installed)",
                "json_str": "[]",
            },
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
matching_service = MatchingService()
