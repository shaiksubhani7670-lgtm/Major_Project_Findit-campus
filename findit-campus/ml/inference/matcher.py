"""
FindIt Campus — Core Matcher
Combines all AI signals into a unified matching engine.
"""

import logging
import numpy as np
from ml.inference.object_detector import ObjectDetector
from ml.inference.feature_extractor import FeatureExtractor
from ml.inference.color_detector import ColorDetector
from ml.inference.text_embedder import TextEmbedder, DescriptionEnhancer
from ml.inference.ocr_reader import OCRReader
from ml.inference.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Matching weights from specification
WEIGHTS = {
    'image': 0.40,
    'text': 0.25,
    'color': 0.10,
    'brand': 0.10,
    'location': 0.10,
    'date': 0.05,
}


class ItemMatcher:
    """
    Core matching engine that combines all AI signals.
    Processes lost and found items through the full pipeline.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.object_detector = None
        self.feature_extractor = None
        self.color_detector = None
        self.text_embedder = None
        self.ocr_reader = None
        self.vector_store = None
        self._initialized = False

    def initialize(self):
        """Lazy-initialize all ML components."""
        if self._initialized:
            return

        logger.info("Initializing ItemMatcher ML pipeline...")

        try:
            self.object_detector = ObjectDetector(
                model_path=self.config.get('yolo_model_path')
            )
        except Exception as e:
            logger.warning(f"ObjectDetector init failed: {e}")

        try:
            self.feature_extractor = FeatureExtractor()
        except Exception as e:
            logger.warning(f"FeatureExtractor init failed: {e}")

        try:
            self.color_detector = ColorDetector()
        except Exception as e:
            logger.warning(f"ColorDetector init failed: {e}")

        try:
            self.text_embedder = TextEmbedder(
                model_name=self.config.get('sentence_model', 'all-MiniLM-L6-v2')
            )
        except Exception as e:
            logger.warning(f"TextEmbedder init failed: {e}")

        try:
            self.ocr_reader = OCRReader()
        except Exception as e:
            logger.warning(f"OCRReader init failed: {e}")

        try:
            self.vector_store = VectorStore(
                dimension=384,
                index_path=self.config.get('faiss_index_path')
            )
        except Exception as e:
            logger.warning(f"VectorStore init failed: {e}")

        self._initialized = True
        logger.info("ItemMatcher initialization complete")

    def process_image(self, image_path):
        """
        Process an uploaded image through the full pipeline.

        Returns:
            dict with all extracted features, detections, colors, OCR text, and embeddings
        """
        self.initialize()
        result = {
            'detections': [],
            'colors': {},
            'features': {},
            'ocr_text': '',
            'ocr_identifiers': {},
            'embedding': None,
        }

        # Step 1: Object Detection (YOLOv8)
        if self.object_detector:
            category, confidence, detections = self.object_detector.detect_and_classify(image_path)
            result['detections'] = detections
            result['detected_category'] = category
            result['detection_confidence'] = confidence

        # Step 2: Feature Extraction (OpenCV)
        if self.feature_extractor:
            features = self.feature_extractor.extract(image_path)
            result['features'] = {
                k: v.tolist() if isinstance(v, np.ndarray) else v
                for k, v in features.items()
                if k != 'combined_vector'
            }
            if 'combined_vector' in features:
                result['feature_vector'] = features['combined_vector']

        # Step 3: Color Detection
        if self.color_detector:
            result['colors'] = self.color_detector.analyze(image_path)

        # Step 4: OCR
        if self.ocr_reader:
            result['ocr_text'] = self.ocr_reader.extract_all_text(image_path)
            result['ocr_identifiers'] = self.ocr_reader.extract_identifiers(image_path)

        return result

    def compute_match_score(self, lost_item, found_item, lost_image_data=None, found_image_data=None):
        """
        Compute the weighted match score between a lost and found item.

        Args:
            lost_item: dict with lost item fields
            found_item: dict with found item fields
            lost_image_data: Pre-processed image data for lost item
            found_image_data: Pre-processed image data for found item

        Returns:
            dict with individual scores and total weighted score
        """
        self.initialize()
        scores = {}

        # 1. Image Similarity (40%)
        scores['image'] = self._compute_image_similarity(lost_image_data, found_image_data)

        # 2. Text Similarity (25%)
        scores['text'] = self._compute_text_similarity(lost_item, found_item)

        # 3. Color Similarity (10%)
        scores['color'] = self._compute_color_similarity(lost_item, found_item)

        # 4. Brand Similarity (10%)
        scores['brand'] = self._compute_brand_similarity(lost_item, found_item)

        # 5. Location Similarity (10%)
        scores['location'] = self._compute_location_similarity(lost_item, found_item)

        # 6. Date Similarity (5%)
        scores['date'] = self._compute_date_similarity(lost_item, found_item)

        # Weighted total (as percentage)
        total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS) * 100
        scores['total'] = round(total, 2)

        # Confidence level
        if total >= 95:
            scores['confidence_level'] = 'very_high'
        elif total >= 80:
            scores['confidence_level'] = 'high'
        elif total >= 65:
            scores['confidence_level'] = 'possible'
        else:
            scores['confidence_level'] = 'low'

        return scores

    def _compute_image_similarity(self, img_data1, img_data2):
        """Image similarity using visual features."""
        if not img_data1 or not img_data2:
            return 0.5

        if self.feature_extractor and 'feature_vector' in img_data1 and 'feature_vector' in img_data2:
            return self.feature_extractor.compute_similarity(
                {'combined_vector': img_data1['feature_vector']},
                {'combined_vector': img_data2['feature_vector']},
            )

        return 0.5

    def _compute_text_similarity(self, item1, item2):
        """Text similarity using sentence embeddings."""
        desc1 = DescriptionEnhancer.enhance_lost_item(item1)
        desc2 = DescriptionEnhancer.enhance_found_item(item2)

        if self.text_embedder:
            return self.text_embedder.similarity(desc1, desc2)

        # Fallback: word overlap
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / max(len(words1), len(words2))

    def _compute_color_similarity(self, item1, item2):
        """Color similarity."""
        color1 = item1.get('primary_color', '')
        color2 = item2.get('manual_color') or item2.get('detected_color', '')
        return ColorDetector.color_similarity(color1, color2)

    def _compute_brand_similarity(self, item1, item2):
        """Brand similarity."""
        brand1 = (item1.get('brand') or '').lower().strip()
        brand2 = (item2.get('brand') or '').lower().strip()

        if not brand1 or not brand2:
            return 0.5

        if brand1 == brand2:
            return 1.0

        if brand1 in brand2 or brand2 in brand1:
            return 0.8

        return 0.0

    def _compute_location_similarity(self, item1, item2):
        """Location similarity."""
        building1 = (item1.get('building') or '').lower()
        building2 = (item2.get('building') or '').lower()
        floor1 = item1.get('floor', '')
        floor2 = item2.get('floor', '')

        if not building1 or not building2:
            return 0.5

        score = 0.0
        factors = 0

        if building1 and building2:
            factors += 2
            score += 2.0 if building1 == building2 else 0.0

        if floor1 and floor2:
            factors += 1
            score += 1.0 if floor1 == floor2 else 0.0

        return score / factors if factors > 0 else 0.5

    def _compute_date_similarity(self, item1, item2):
        """Date proximity similarity."""
        from datetime import date as Date

        date1 = item1.get('lost_date')
        date2 = item2.get('found_date')

        if not date1 or not date2:
            return 0.5

        if isinstance(date1, str):
            date1 = Date.fromisoformat(date1)
        if isinstance(date2, str):
            date2 = Date.fromisoformat(date2)

        days_diff = abs((date2 - date1).days)

        if days_diff == 0:
            return 1.0
        elif days_diff <= 1:
            return 0.9
        elif days_diff <= 3:
            return 0.7
        elif days_diff <= 7:
            return 0.5
        elif days_diff <= 14:
            return 0.3
        else:
            return 0.1


# Singleton
matcher = ItemMatcher()
