"""
ocr.py
Local-only OCR pipeline: OpenCV preprocessing (grayscale, deskew,
adaptive threshold, contrast boost) followed by Tesseract text
extraction via pytesseract. No network calls are made anywhere in
this module, per Marcus's firewall constraint.
"""

import cv2
import numpy as np
import pytesseract

from app.utils import downscale_if_needed, timed


def _grayscale(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _boost_contrast(gray: np.ndarray) -> np.ndarray:
    """CLAHE contrast boost to help with low-lighting label photos."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Estimate and correct small rotational skew using the minAreaRect
    of thresholded foreground pixels. Falls back to the original image
    if no usable text-like contour is found.
    """
    inverted = cv2.bitwise_not(gray)
    thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = cv2.findNonZero(thresh)
    if coords is None:
        return gray

    angle = cv2.minAreaRect(coords)[-1]
    # cv2.minAreaRect returns angles in [-90, 0); normalize to a small
    # rotation correction rather than a full re-orientation.
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.5:
        # Not worth rotating for sub-degree skew.
        return gray

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        gray, matrix, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def _adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Full preprocessing pipeline: downscale -> grayscale -> deskew ->
    contrast boost -> adaptive threshold. Returns an image ready for
    Tesseract.
    """
    image = downscale_if_needed(image)
    gray = _grayscale(image)
    deskewed = _deskew(gray)
    contrasted = _boost_contrast(deskewed)
    thresholded = _adaptive_threshold(contrasted)
    return thresholded


@timed
def extract_text(image: np.ndarray) -> str:
    """Preprocess an image and run local Tesseract OCR on it.

    Wrapped in @timed so callers get back (text, elapsed_seconds) —
    used to surface the per-image timing metric required by the
    non-functional requirements.
    """
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(processed)
    return text
