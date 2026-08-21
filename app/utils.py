"""
utils.py
Small shared helpers used across the app: timing instrumentation and
image downscaling to keep OCR within the ~5 second target.
"""

import time
import functools

import cv2
import numpy as np

# Any image with a max dimension above this gets downscaled before OCR.
MAX_DIMENSION_PX = 1600


def timed(func):
    """Decorator that returns (result, elapsed_seconds) instead of just result.

    Used so every processed image can report a timing metric, per the
    non-functional requirement to surface timing per image.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return result, elapsed
    return wrapper


def downscale_if_needed(image: np.ndarray, max_dim: int = MAX_DIMENSION_PX) -> np.ndarray:
    """Downscale an image so its largest dimension does not exceed max_dim.

    Large phone-camera images slow OCR down significantly. Downscaling
    before preprocessing keeps per-image processing close to the
    5-second target agreed with Sarah Chen.
    """
    height, width = image.shape[:2]
    largest = max(height, width)
    if largest <= max_dim:
        return image

    scale = max_dim / float(largest)
    new_size = (int(width * scale), int(height * scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def read_image_bytes(data: bytes) -> np.ndarray:
    """Decode raw image bytes (as uploaded) into an OpenCV BGR image."""
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image file. Unsupported or corrupt image.")
    return image
