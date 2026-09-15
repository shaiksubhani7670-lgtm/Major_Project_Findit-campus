"""
FindIt Campus — Color Detector
Analyzes images to extract dominant and secondary colors using HSV color space.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

# HSV color ranges for common colors
COLOR_RANGES = {
    'Red': [
        ((0, 70, 50), (10, 255, 255)),
        ((170, 70, 50), (180, 255, 255)),
    ],
    'Orange': [((10, 70, 50), (25, 255, 255))],
    'Yellow': [((25, 70, 50), (35, 255, 255))],
    'Green': [((35, 70, 50), (85, 255, 255))],
    'Cyan': [((85, 70, 50), (100, 255, 255))],
    'Blue': [((100, 70, 50), (130, 255, 255))],
    'Purple': [((130, 70, 50), (155, 255, 255))],
    'Pink': [((155, 70, 50), (170, 255, 255))],
    'White': [((0, 0, 200), (180, 30, 255))],
    'Grey': [((0, 0, 80), (180, 30, 200))],
    'Black': [((0, 0, 0), (180, 30, 80))],
    'Brown': [((10, 70, 50), (20, 255, 150))],
    'Silver': [((0, 0, 170), (180, 20, 230))],
    'Gold': [((20, 70, 100), (30, 255, 255))],
    'Navy': [((100, 70, 30), (130, 255, 120))],
    'Maroon': [((0, 70, 30), (10, 255, 120))],
}


class ColorDetector:
    """
    Detects dominant and secondary colors in images using HSV analysis.
    Provides color names, percentages, and similarity scoring.
    """

    def __init__(self):
        """Initialize the color detector."""
        try:
            import cv2
            self.cv2 = cv2
            logger.info("ColorDetector initialized with OpenCV")
        except ImportError:
            self.cv2 = None
            logger.warning("OpenCV not available. ColorDetector will use fallback mode.")

    def analyze(self, image_path_or_array):
        """
        Analyze an image and extract color information.

        Args:
            image_path_or_array: Path to image file or numpy array (BGR format)

        Returns:
            dict with keys: dominant_color, secondary_color, color_percentages, palette
        """
        if self.cv2 is None:
            return self._fallback_result()

        try:
            # Load image
            if isinstance(image_path_or_array, str):
                image = self.cv2.imread(image_path_or_array)
            else:
                image = image_path_or_array

            if image is None:
                logger.error("Failed to load image")
                return self._fallback_result()

            # Resize for faster processing
            image = self.cv2.resize(image, (300, 300))

            # Convert to HSV
            hsv = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2HSV)

            # Calculate color percentages
            total_pixels = hsv.shape[0] * hsv.shape[1]
            color_counts = {}

            for color_name, ranges in COLOR_RANGES.items():
                mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
                for lower, upper in ranges:
                    lower_np = np.array(lower, dtype=np.uint8)
                    upper_np = np.array(upper, dtype=np.uint8)
                    mask = mask | self.cv2.inRange(hsv, lower_np, upper_np)

                count = int(np.sum(mask > 0))
                percentage = round((count / total_pixels) * 100, 1)
                if percentage > 1:  # Only include colors above 1%
                    color_counts[color_name] = percentage

            # Sort by percentage
            sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)

            if not sorted_colors:
                return self._fallback_result()

            dominant_color = sorted_colors[0][0]
            secondary_color = sorted_colors[1][0] if len(sorted_colors) > 1 else None

            # Extract color palette using K-Means clustering
            palette = self._extract_palette(image, k=5)

            result = {
                'dominant_color': dominant_color,
                'dominant_percentage': sorted_colors[0][1],
                'secondary_color': secondary_color,
                'secondary_percentage': sorted_colors[1][1] if len(sorted_colors) > 1 else 0,
                'color_percentages': dict(sorted_colors[:5]),
                'palette': palette,
            }

            logger.info(f"Color analysis complete: {dominant_color} ({sorted_colors[0][1]}%)")
            return result

        except Exception as e:
            logger.error(f"Color analysis failed: {e}")
            return self._fallback_result()

    def _extract_palette(self, image, k=5):
        """Extract top-k color palette using K-Means clustering."""
        try:
            from sklearn.cluster import KMeans

            # Reshape image to pixel list
            pixels = image.reshape(-1, 3).astype(np.float32)

            # Run K-Means
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(pixels)

            # Get cluster centers (BGR colors)
            centers = kmeans.cluster_centers_.astype(int)

            # Count pixels per cluster
            labels, counts = np.unique(kmeans.labels_, return_counts=True)
            total = sum(counts)

            palette = []
            for center, count in sorted(zip(centers, counts), key=lambda x: x[1], reverse=True):
                # Convert BGR to RGB hex
                r, g, b = int(center[2]), int(center[1]), int(center[0])
                hex_color = f'#{r:02x}{g:02x}{b:02x}'
                palette.append({
                    'hex': hex_color,
                    'rgb': [r, g, b],
                    'percentage': round((count / total) * 100, 1),
                })

            return palette

        except Exception as e:
            logger.warning(f"Palette extraction failed: {e}")
            return []

    @staticmethod
    def color_similarity(color1, color2):
        """
        Calculate similarity between two color names.

        Returns:
            float between 0.0 and 1.0
        """
        if not color1 or not color2:
            return 0.5  # Neutral

        if color1.lower() == color2.lower():
            return 1.0

        # Similar color groups
        color_groups = {
            'warm': {'red', 'orange', 'yellow', 'brown', 'gold', 'maroon'},
            'cool': {'blue', 'cyan', 'purple', 'navy'},
            'neutral': {'white', 'grey', 'silver', 'black'},
            'nature': {'green', 'brown'},
        }

        c1_lower = color1.lower()
        c2_lower = color2.lower()

        for group_colors in color_groups.values():
            if c1_lower in group_colors and c2_lower in group_colors:
                return 0.6  # Same color family

        return 0.0

    @staticmethod
    def _fallback_result():
        """Return a neutral result when analysis isn't possible."""
        return {
            'dominant_color': None,
            'dominant_percentage': 0,
            'secondary_color': None,
            'secondary_percentage': 0,
            'color_percentages': {},
            'palette': [],
        }
