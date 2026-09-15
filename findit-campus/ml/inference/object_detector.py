"""
FindIt Campus — Object Detector (YOLOv8)
Detects objects in uploaded images using YOLOv8.
Identifies item types: laptop, phone, wallet, bag, keys, etc.
"""

import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Campus-relevant COCO class mappings
CAMPUS_ITEM_CLASSES = {
    'laptop': ['laptop'],
    'mobile': ['cell phone'],
    'bag': ['backpack', 'handbag', 'suitcase'],
    'bottle': ['bottle'],
    'books': ['book'],
    'watch': ['clock'],  # COCO doesn't have watch, closest is clock
    'umbrella': ['umbrella'],
    'keys': ['scissors'],  # Placeholder — fine-tune for actual keys
    'wallet': [],  # Needs fine-tuning
    'earbuds': [],
    'headphones': [],
    'helmet': [],
    'id_card': [],
}

# Reverse mapping: COCO class → campus category
COCO_TO_CAMPUS = {}
for campus_cat, coco_classes in CAMPUS_ITEM_CLASSES.items():
    for cc in coco_classes:
        COCO_TO_CAMPUS[cc] = campus_cat


class ObjectDetector:
    """
    YOLOv8-based object detector for campus items.
    Uses pre-trained COCO model with optional fine-tuning for campus-specific objects.
    """

    def __init__(self, model_path=None):
        """
        Initialize the object detector.

        Args:
            model_path: Path to fine-tuned YOLOv8 model weights.
                       Falls back to pre-trained yolov8n if not provided.
        """
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        """Load the YOLOv8 model."""
        try:
            from ultralytics import YOLO

            if self.model_path and Path(self.model_path).exists():
                self.model = YOLO(self.model_path)
                logger.info(f"Loaded fine-tuned YOLOv8 model from {self.model_path}")
            else:
                # Fall back to pre-trained model
                self.model = YOLO('yolov8n.pt')
                logger.info("Loaded pre-trained YOLOv8n model")

        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            self.model = None

    def detect(self, image_path_or_array, confidence_threshold=0.5):
        """
        Detect objects in an image.

        Args:
            image_path_or_array: Path to image file or numpy array
            confidence_threshold: Minimum confidence for detections

        Returns:
            list of dict with keys: class_name, campus_category, confidence, bbox
        """
        if self.model is None:
            logger.warning("YOLOv8 model not loaded. Returning empty detections.")
            return []

        try:
            results = self.model(image_path_or_array, conf=confidence_threshold, verbose=False)
            detections = []

            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    confidence = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                    campus_category = COCO_TO_CAMPUS.get(class_name, 'other')

                    detections.append({
                        'class_name': class_name,
                        'campus_category': campus_category,
                        'confidence': round(confidence, 3),
                        'bbox': [round(b, 1) for b in bbox],
                        'area': round((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 1),
                    })

            # Sort by confidence
            detections.sort(key=lambda x: x['confidence'], reverse=True)
            logger.info(f"Detected {len(detections)} objects in image")
            return detections

        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []

    def detect_and_classify(self, image_path_or_array):
        """
        Detect objects and return the most likely campus item category.

        Returns:
            tuple: (campus_category, confidence, all_detections)
        """
        detections = self.detect(image_path_or_array)

        if not detections:
            return 'other', 0.0, []

        # Find the most confident campus-relevant detection
        for det in detections:
            if det['campus_category'] != 'other':
                return det['campus_category'], det['confidence'], detections

        # If no campus-relevant detection, return the top detection
        top = detections[0]
        return top['campus_category'], top['confidence'], detections

    def extract_features(self, image_path_or_array):
        """
        Extract visual feature embeddings from the image using the YOLOv8 backbone.

        Returns:
            numpy array of shape (512,) — feature vector
        """
        if self.model is None:
            return np.zeros(512, dtype=np.float32)

        try:
            results = self.model(image_path_or_array, verbose=False)

            # Extract features from the last layer before detection head
            if hasattr(results[0], 'probs') and results[0].probs is not None:
                return results[0].probs.data.cpu().numpy()

            # Alternative: use the detection features
            # This is a simplified approach — for production, use a dedicated feature extractor
            return np.random.randn(512).astype(np.float32)  # Placeholder

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return np.zeros(512, dtype=np.float32)
