"""
FindIt Campus — Feature Extractor (OpenCV)
Extracts visual features: shape, texture, edges, patterns, color histogram, and size.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    OpenCV-based visual feature extractor.
    Extracts shape, texture, edges, patterns, color histograms, and size information.
    """

    def __init__(self):
        """Initialize the feature extractor."""
        try:
            import cv2
            self.cv2 = cv2
            logger.info("FeatureExtractor initialized with OpenCV")
        except ImportError:
            self.cv2 = None
            logger.warning("OpenCV not available.")

    def extract(self, image_path_or_array):
        """
        Extract comprehensive visual features from an image.

        Args:
            image_path_or_array: Path to image or numpy array (BGR)

        Returns:
            dict with feature categories and a combined feature vector
        """
        if self.cv2 is None:
            return self._empty_features()

        try:
            # Load image
            if isinstance(image_path_or_array, str):
                image = self.cv2.imread(image_path_or_array)
            else:
                image = image_path_or_array.copy()

            if image is None:
                return self._empty_features()

            # Resize for consistent feature extraction
            image = self.cv2.resize(image, (256, 256))
            gray = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2GRAY)

            features = {
                'color_histogram': self._color_histogram(image),
                'edge_features': self._edge_features(gray),
                'texture_features': self._texture_features(gray),
                'shape_features': self._shape_features(gray),
                'size_features': self._size_features(image),
                'hu_moments': self._hu_moments(gray),
            }

            # Combine into a single feature vector
            combined = np.concatenate([
                features['color_histogram'],
                features['edge_features'],
                features['texture_features'],
                features['hu_moments'],
            ])

            features['combined_vector'] = combined.astype(np.float32)
            features['vector_dim'] = len(combined)

            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return self._empty_features()

    def _color_histogram(self, image):
        """Extract normalized color histogram in HSV space."""
        hsv = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2HSV)

        # Calculate histograms for H, S, V channels
        h_hist = self.cv2.calcHist([hsv], [0], None, [32], [0, 180])
        s_hist = self.cv2.calcHist([hsv], [1], None, [32], [0, 256])
        v_hist = self.cv2.calcHist([hsv], [2], None, [32], [0, 256])

        # Normalize
        self.cv2.normalize(h_hist, h_hist)
        self.cv2.normalize(s_hist, s_hist)
        self.cv2.normalize(v_hist, v_hist)

        return np.concatenate([h_hist, s_hist, v_hist]).flatten()

    def _edge_features(self, gray):
        """Extract edge features using Canny edge detection."""
        edges = self.cv2.Canny(gray, 50, 150)

        # Edge density
        edge_density = np.sum(edges > 0) / edges.size

        # Edge direction histogram
        sobelx = self.cv2.Sobel(gray, self.cv2.CV_64F, 1, 0, ksize=3)
        sobely = self.cv2.Sobel(gray, self.cv2.CV_64F, 0, 1, ksize=3)
        angles = np.arctan2(sobely, sobelx)
        angle_hist, _ = np.histogram(angles, bins=16, range=(-np.pi, np.pi))
        angle_hist = angle_hist.astype(np.float32)
        angle_hist = angle_hist / (angle_hist.sum() + 1e-8)

        return np.concatenate([[edge_density], angle_hist])

    def _texture_features(self, gray):
        """Extract texture features using Local Binary Pattern-style analysis."""
        # Simple texture features using Gabor filters
        features = []

        for theta in [0, np.pi/4, np.pi/2, 3*np.pi/4]:
            kernel = self.cv2.getGaborKernel(
                (21, 21), sigma=5, theta=theta,
                lambd=10, gamma=0.5, psi=0
            )
            filtered = self.cv2.filter2D(gray, self.cv2.CV_64F, kernel)
            features.extend([
                float(np.mean(filtered)),
                float(np.std(filtered)),
            ])

        return np.array(features, dtype=np.float32)

    def _shape_features(self, gray):
        """Extract shape features from contours."""
        _, thresh = self.cv2.threshold(gray, 0, 255, self.cv2.THRESH_BINARY + self.cv2.THRESH_OTSU)
        contours, _ = self.cv2.findContours(thresh, self.cv2.RETR_EXTERNAL, self.cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {'contour_count': 0, 'largest_area': 0, 'circularity': 0}

        largest = max(contours, key=self.cv2.contourArea)
        area = self.cv2.contourArea(largest)
        perimeter = self.cv2.arcLength(largest, True)
        circularity = (4 * np.pi * area / (perimeter ** 2 + 1e-8)) if perimeter > 0 else 0

        return {
            'contour_count': len(contours),
            'largest_area': float(area),
            'circularity': float(circularity),
            'aspect_ratio': self._aspect_ratio(largest),
        }

    def _aspect_ratio(self, contour):
        """Calculate aspect ratio of the bounding rectangle."""
        x, y, w, h = self.cv2.boundingRect(contour)
        return float(w) / (h + 1e-8)

    def _size_features(self, image):
        """Extract size-related features."""
        return {
            'width': image.shape[1],
            'height': image.shape[0],
            'aspect_ratio': image.shape[1] / (image.shape[0] + 1e-8),
        }

    def _hu_moments(self, gray):
        """Extract Hu moments (rotation-invariant shape descriptors)."""
        moments = self.cv2.moments(gray)
        hu = self.cv2.HuMoments(moments).flatten()
        # Log transform for better numerical stability
        hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)
        return hu.astype(np.float32)

    def compute_similarity(self, features1, features2):
        """
        Compute similarity between two feature sets.

        Returns:
            float between 0.0 and 1.0
        """
        if 'combined_vector' not in features1 or 'combined_vector' not in features2:
            return 0.5

        vec1 = features1['combined_vector']
        vec2 = features2['combined_vector']

        if len(vec1) != len(vec2):
            return 0.5

        # Cosine similarity
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(max(0.0, cosine_sim))

    @staticmethod
    def _empty_features():
        """Return empty feature set."""
        return {
            'color_histogram': np.zeros(96, dtype=np.float32),
            'edge_features': np.zeros(17, dtype=np.float32),
            'texture_features': np.zeros(8, dtype=np.float32),
            'shape_features': {'contour_count': 0, 'largest_area': 0, 'circularity': 0},
            'size_features': {'width': 0, 'height': 0, 'aspect_ratio': 0},
            'hu_moments': np.zeros(7, dtype=np.float32),
            'combined_vector': np.zeros(128, dtype=np.float32),
            'vector_dim': 128,
        }
