"""
FindIt Campus — Text Embedder (Sentence Transformers)
Converts text descriptions into dense vector embeddings for semantic similarity.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class TextEmbedder:
    """
    Sentence Transformer-based text embedder for semantic similarity.
    Encodes descriptions like "Blue Wildcraft Bag" and "Dark Blue Wildcraft Backpack"
    as vectors that capture semantic meaning.
    """

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the text embedder.

        Args:
            model_name: HuggingFace model name for sentence-transformers
        """
        self.model = None
        self.model_name = model_name
        self._load_model()

    def _load_model(self):
        """Load the Sentence Transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded Sentence Transformer: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load Sentence Transformer: {e}")
            self.model = None

    def encode(self, text):
        """
        Encode a text string into a dense vector embedding.

        Args:
            text: Input text string

        Returns:
            numpy array of shape (384,) for MiniLM
        """
        if self.model is None:
            logger.warning("Model not loaded. Returning zero vector.")
            return np.zeros(384, dtype=np.float32)

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Text encoding failed: {e}")
            return np.zeros(384, dtype=np.float32)

    def encode_batch(self, texts):
        """
        Encode a batch of texts into embeddings.

        Args:
            texts: List of text strings

        Returns:
            numpy array of shape (n, 384)
        """
        if self.model is None:
            return np.zeros((len(texts), 384), dtype=np.float32)

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Batch encoding failed: {e}")
            return np.zeros((len(texts), 384), dtype=np.float32)

    def similarity(self, text1, text2):
        """
        Calculate cosine similarity between two texts.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            float between 0.0 and 1.0 (cosine similarity, clamped to non-negative)
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        return self._cosine_similarity(emb1, emb2)

    def find_most_similar(self, query_text, candidate_texts, top_k=5):
        """
        Find the most similar texts to a query from a list of candidates.

        Args:
            query_text: Query text string
            candidate_texts: List of candidate text strings
            top_k: Number of top results to return

        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        query_emb = self.encode(query_text)
        candidate_embs = self.encode_batch(candidate_texts)

        similarities = []
        for i, cand_emb in enumerate(candidate_embs):
            sim = self._cosine_similarity(query_emb, cand_emb)
            similarities.append((i, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    @staticmethod
    def _cosine_similarity(vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = float(np.dot(vec1, vec2) / (norm1 * norm2))
        return max(0.0, similarity)  # Clamp to non-negative


class DescriptionEnhancer:
    """
    Enhances item descriptions for better matching.
    Combines structured fields into a rich text description.
    """

    @staticmethod
    def enhance_lost_item(item):
        """
        Create an enhanced description from a lost item's fields.

        Args:
            item: LostItem model instance or dict

        Returns:
            Enhanced description string
        """
        if isinstance(item, dict):
            parts = [
                item.get('item_name', ''),
                f"Category: {item.get('category', '')}",
                f"Brand: {item.get('brand', '')}" if item.get('brand') else '',
                f"Color: {item.get('primary_color', '')}" if item.get('primary_color') else '',
                f"Material: {item.get('material', '')}" if item.get('material') else '',
                item.get('description', ''),
                f"Location: {item.get('building', '')} {item.get('floor', '')} {item.get('room_number', '')}",
            ]
        else:
            parts = [
                item.item_name,
                f"Category: {item.category.value}",
                f"Brand: {item.brand}" if item.brand else '',
                f"Color: {item.primary_color}" if item.primary_color else '',
                f"Material: {item.material}" if item.material else '',
                item.description,
                f"Location: {item.building or ''} {item.floor or ''} {item.room_number or ''}",
            ]

        return ' '.join(p for p in parts if p).strip()

    @staticmethod
    def enhance_found_item(item):
        """Create an enhanced description from a found item's fields."""
        if isinstance(item, dict):
            parts = [
                item.get('item_name', ''),
                f"Category: {item.get('category', '')}",
                f"Brand: {item.get('brand', '')}" if item.get('brand') else '',
                f"Color: {item.get('manual_color', '') or item.get('detected_color', '')}",
                f"Material: {item.get('material', '')}" if item.get('material') else '',
                item.get('description', ''),
                f"Location: {item.get('building', '')} {item.get('floor', '')} {item.get('room_number', '')}",
            ]
        else:
            parts = [
                item.item_name,
                f"Category: {item.category.value}",
                f"Brand: {item.brand}" if item.brand else '',
                f"Color: {item.manual_color or item.detected_color or ''}",
                f"Material: {item.material}" if item.material else '',
                item.description,
                f"Location: {item.building or ''} {item.floor or ''} {item.room_number or ''}",
            ]

        return ' '.join(p for p in parts if p).strip()
