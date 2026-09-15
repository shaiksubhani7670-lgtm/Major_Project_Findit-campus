"""
FindIt Campus — OCR Reader (EasyOCR)
Extracts text from item images — names, roll numbers, stickers, labels, etc.
"""

import logging

logger = logging.getLogger(__name__)


class OCRReader:
    """
    EasyOCR-based text extraction from item images.
    Reads names, roll numbers, stickers, book titles, laptop labels, ID card text.
    """

    def __init__(self, languages=None):
        """
        Initialize the OCR reader.

        Args:
            languages: List of language codes (default: ['en'])
        """
        self.reader = None
        self.languages = languages or ['en']
        self._load_reader()

    def _load_reader(self):
        """Load the EasyOCR reader."""
        try:
            import easyocr
            self.reader = easyocr.Reader(self.languages, gpu=False)
            logger.info(f"EasyOCR reader loaded for languages: {self.languages}")
        except Exception as e:
            logger.error(f"Failed to load EasyOCR: {e}")
            self.reader = None

    def read_text(self, image_path_or_array, detail=True):
        """
        Extract text from an image.

        Args:
            image_path_or_array: Path to image file or numpy array
            detail: If True, return detailed results with bounding boxes

        Returns:
            If detail=True: list of (bbox, text, confidence) tuples
            If detail=False: list of text strings
        """
        if self.reader is None:
            logger.warning("EasyOCR not loaded. Returning empty results.")
            return []

        try:
            results = self.reader.readtext(image_path_or_array)

            if detail:
                return [
                    {
                        'bbox': [[int(p[0]), int(p[1])] for p in bbox],
                        'text': text,
                        'confidence': round(float(conf), 3),
                    }
                    for bbox, text, conf in results
                ]
            else:
                return [text for _, text, _ in results]

        except Exception as e:
            logger.error(f"OCR reading failed: {e}")
            return []

    def extract_identifiers(self, image_path_or_array):
        """
        Extract identity-related text from an image.
        Specifically looks for names, roll numbers, and identifying labels.

        Returns:
            dict with extracted identifiers
        """
        import re

        texts = self.read_text(image_path_or_array, detail=False)
        full_text = ' '.join(texts)

        identifiers = {
            'raw_text': full_text,
            'roll_numbers': [],
            'names': [],
            'labels': [],
            'phone_numbers': [],
        }

        for text in texts:
            text_clean = text.strip()

            # Detect roll numbers (alphanumeric patterns like CSE2021001)
            roll_pattern = re.findall(r'[A-Z]{2,5}\d{4,}', text_clean.upper())
            identifiers['roll_numbers'].extend(roll_pattern)

            # Detect phone numbers
            phone_pattern = re.findall(r'\+?\d{10,13}', text_clean.replace(' ', ''))
            identifiers['phone_numbers'].extend(phone_pattern)

            # Other text is treated as labels/names
            if len(text_clean) >= 3 and not roll_pattern and not phone_pattern:
                identifiers['labels'].append(text_clean)

        return identifiers

    def extract_all_text(self, image_path_or_array):
        """
        Extract all text from image as a single string.

        Returns:
            str: Concatenated text from image
        """
        texts = self.read_text(image_path_or_array, detail=False)
        return ' '.join(texts).strip()
