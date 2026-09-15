"""
FindIt Campus — Vector Store (FAISS)
Stores and searches text/image embeddings using Facebook AI Similarity Search.
"""

import logging
import os
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS-based vector store for fast nearest-neighbor search.
    Used for finding similar item descriptions and images.
    """

    def __init__(self, dimension=384, index_path=None):
        """
        Initialize the vector store.

        Args:
            dimension: Embedding dimension (384 for MiniLM, 512 for image features)
            index_path: Path to load/save the FAISS index
        """
        self.dimension = dimension
        self.index_path = index_path
        self.index = None
        self.id_map = {}  # Maps FAISS internal ID → item ID
        self.faiss = None

        self._init_faiss()

    def _init_faiss(self):
        """Initialize FAISS index."""
        try:
            import faiss
            self.faiss = faiss

            # Try to load existing index
            if self.index_path and os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded FAISS index from {self.index_path} ({self.index.ntotal} vectors)")
            else:
                # Create new index with L2 distance
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine similarity)
                logger.info(f"Created new FAISS index (dimension={self.dimension})")

        except ImportError:
            logger.warning("FAISS not available. Using brute-force search.")
            self.index = None

    def add(self, item_id, embedding):
        """
        Add a single embedding to the index.

        Args:
            item_id: Unique identifier for the item
            embedding: numpy array of shape (dimension,)
        """
        if self.index is None:
            self.id_map[len(self.id_map)] = item_id
            return

        # Normalize for cosine similarity
        embedding = self._normalize(embedding.reshape(1, -1))

        faiss_id = self.index.ntotal
        self.index.add(embedding)
        self.id_map[faiss_id] = item_id

        logger.debug(f"Added embedding for item {item_id} (FAISS ID: {faiss_id})")

    def add_batch(self, item_ids, embeddings):
        """
        Add multiple embeddings to the index.

        Args:
            item_ids: List of unique identifiers
            embeddings: numpy array of shape (n, dimension)
        """
        if self.index is None:
            for item_id in item_ids:
                self.id_map[len(self.id_map)] = item_id
            return

        embeddings = self._normalize(embeddings)

        start_id = self.index.ntotal
        self.index.add(embeddings)

        for i, item_id in enumerate(item_ids):
            self.id_map[start_id + i] = item_id

        logger.info(f"Added {len(item_ids)} embeddings to index (total: {self.index.ntotal})")

    def search(self, query_embedding, top_k=10):
        """
        Search for the most similar embeddings.

        Args:
            query_embedding: numpy array of shape (dimension,)
            top_k: Number of nearest neighbors to return

        Returns:
            List of (item_id, similarity_score) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        query = self._normalize(query_embedding.reshape(1, -1))

        # Search
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            item_id = self.id_map.get(int(idx))
            if item_id is not None:
                results.append((item_id, float(score)))

        return results

    def remove(self, item_id):
        """
        Remove an item from the index.
        Note: FAISS IndexFlatIP doesn't support direct removal.
        We mark it as removed in the id_map.
        """
        for faiss_id, mapped_id in list(self.id_map.items()):
            if mapped_id == item_id:
                del self.id_map[faiss_id]
                logger.debug(f"Removed item {item_id} from id_map")
                return True
        return False

    def save(self, path=None):
        """Save the index to disk."""
        save_path = path or self.index_path
        if save_path and self.index is not None:
            self.faiss.write_index(self.index, save_path)
            logger.info(f"Saved FAISS index to {save_path}")

    def clear(self):
        """Clear the index."""
        if self.faiss:
            self.index = self.faiss.IndexFlatIP(self.dimension)
        self.id_map = {}
        logger.info("Cleared FAISS index")

    @property
    def size(self):
        """Return the number of vectors in the index."""
        if self.index is None:
            return len(self.id_map)
        return self.index.ntotal

    @staticmethod
    def _normalize(vectors):
        """L2 normalize vectors for cosine similarity."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return (vectors / norms).astype(np.float32)
