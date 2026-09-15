"""
FindIt Campus — ML Inference Package  (Expert v3.0)

v3 Modules (primary pipeline):
  bge_embedder / sbert_embedder  → BGE-small-en-v1.5 text encoder
  siglip_matcher / clip_matcher  → SigLIP cross-modal image matcher
  blip_captioner                 → BLIP image captioner (fallback enrichment)
  multimodal_matcher             → Unified weighted scorer
  bm25_retriever                 → BM25 keyword pre-filter + RRF fusion
  explainer                      → Human-readable match explanation generator

v1 Legacy modules (retained, not removed):
  text_embedder, feature_extractor, color_detector, vector_store,
  object_detector, ocr_reader
"""

# ---------------------------------------------------------------------------
# v3 primary modules
# ---------------------------------------------------------------------------
try:
    from ml.inference.sbert_embedder   import BGEEmbedder, bge_embedder, sbert_embedder   # noqa: F401
except ImportError:
    BGEEmbedder = bge_embedder = sbert_embedder = None

try:
    from ml.inference.clip_matcher     import SigLIPMatcher, siglip_matcher, clip_matcher  # noqa: F401
except ImportError:
    SigLIPMatcher = siglip_matcher = clip_matcher = None

try:
    from ml.inference.blip_captioner   import BLIPCaptioner, blip_captioner                # noqa: F401
except ImportError:
    BLIPCaptioner = blip_captioner = None

try:
    from ml.inference.multimodal_matcher import MultimodalMatcher, multimodal_matcher      # noqa: F401
except ImportError:
    MultimodalMatcher = multimodal_matcher = None

try:
    from ml.inference.bm25_retriever   import BM25Retriever, bm25_retriever, reciprocal_rank_fusion  # noqa: F401
except ImportError:
    BM25Retriever = bm25_retriever = reciprocal_rank_fusion = None

try:
    from ml.inference.explainer        import MatchExplainer, match_explainer              # noqa: F401
except ImportError:
    MatchExplainer = match_explainer = None

# ---------------------------------------------------------------------------
# v1 legacy modules (kept for reference, not used by v3 pipeline)
# ---------------------------------------------------------------------------
try:
    from ml.inference.text_embedder    import TextEmbedder, DescriptionEnhancer            # noqa: F401
except ImportError:
    TextEmbedder = DescriptionEnhancer = None

try:
    from ml.inference.feature_extractor import FeatureExtractor                             # noqa: F401
except ImportError:
    FeatureExtractor = None

try:
    from ml.inference.color_detector   import ColorDetector                                # noqa: F401
except ImportError:
    ColorDetector = None

try:
    from ml.inference.vector_store     import VectorStore                                  # noqa: F401
except ImportError:
    VectorStore = None

try:
    from ml.inference.object_detector  import ObjectDetector                               # noqa: F401
except ImportError:
    ObjectDetector = None

try:
    from ml.inference.ocr_reader       import OCRReader                                    # noqa: F401
except ImportError:
    OCRReader = None

__all__ = [
    # v3 primary
    "BGEEmbedder", "bge_embedder", "sbert_embedder",
    "SigLIPMatcher", "siglip_matcher", "clip_matcher",
    "BLIPCaptioner", "blip_captioner",
    "MultimodalMatcher", "multimodal_matcher",
    "BM25Retriever", "bm25_retriever", "reciprocal_rank_fusion",
    "MatchExplainer", "match_explainer",
    # v1 legacy
    "TextEmbedder", "DescriptionEnhancer",
    "FeatureExtractor",
    "ColorDetector",
    "VectorStore",
    "ObjectDetector",
    "OCRReader",
]
