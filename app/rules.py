"""
rules.py
The three verification rules: Brand Name, ABV, Government Warning.
Each rule returns a dict with a "status" of PASS / REVIEW / FAIL plus
supporting detail so agents can see why a rule landed where it did.

Threshold logic and canonical text are fixed per the spec and must
not be altered without an explicit requirement change.
"""

import os
import re
import string
from typing import Optional

from rapidfuzz import fuzz

# ---------------------------------------------------------------------------
# Canonical warning text
# ---------------------------------------------------------------------------

_CANONICAL_PATH = os.path.join(os.path.dirname(__file__), "canonical_warning.txt")


def _load_canonical_warning() -> str:
    with open(_CANONICAL_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


CANONICAL_WARNING = _load_canonical_warning()

# ---------------------------------------------------------------------------
# Brand Name Rule
# ---------------------------------------------------------------------------

BRAND_PASS_THRESHOLD = 90
BRAND_REVIEW_THRESHOLD = 80

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)


def normalize_brand(text: str) -> str:
    """Uppercase, strip punctuation, compress whitespace."""
    upper = text.upper()
    no_punct = upper.translate(_PUNCT_TABLE)
    compressed = re.sub(r"\s+", " ", no_punct).strip()
    return compressed


def check_brand(expected_brand: str, ocr_text: str) -> dict:
    """Fuzzy-match the expected brand against the full OCR text.

    Uses RapidFuzz partial_ratio since the brand is typically a
    substring of the full label text rather than the whole text.
    """
    normalized_expected = normalize_brand(expected_brand)
    normalized_ocr = normalize_brand(ocr_text)

    score = fuzz.partial_ratio(normalized_expected, normalized_ocr)

    if score >= BRAND_PASS_THRESHOLD:
        status = "PASS"
    elif score >= BRAND_REVIEW_THRESHOLD:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "rule": "brand_name",
        "status": status,
        "score": round(score, 2),
        "expected": expected_brand,
        "normalized_expected": normalized_expected,
        "override_available": True,
    }


def apply_brand_override(result: dict) -> dict:
    """Agent-triggered override: force brand rule to PASS.

    Dave's requirement — agents may know a name is correct even when
    OCR/fuzzy-matching disagrees (e.g. unusual apostrophe handling).
    """
    overridden = dict(result)
    overridden["status"] = "PASS"
    overridden["overridden_by_agent"] = True
    return overridden

# ---------------------------------------------------------------------------
# ABV Rule
# ---------------------------------------------------------------------------

DEFAULT_ABV_TOLERANCE = 0.1

# Matches things like "ABV 12.5%", "ALC BY VOL 12.5%", "12.5% ABV", etc.
_ABV_PATTERN = re.compile(
    r"(?:(?P<pct_before>\d{1,2}(?:\.\d{1,2})?)\s*%\s*(?:ALC(?:OHOL)?\s*(?:BY)?\s*VOL(?:UME)?|ABV))"
    r"|(?:(?:ALC(?:OHOL)?\s*(?:BY)?\s*VOL(?:UME)?|ABV)\D{0,10}?(?P<pct_after>\d{1,2}(?:\.\d{1,2})?)\s*%)",
    re.IGNORECASE,
)


def extract_abv(ocr_text: str) -> Optional[float]:
    """Extract the ABV percentage nearest an ABV/ALC BY VOL label."""
    match = _ABV_PATTERN.search(ocr_text)
    if not match:
        return None
    value = match.group("pct_before") or match.group("pct_after")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def check_abv(expected_abv: float, ocr_text: str, tolerance: float = DEFAULT_ABV_TOLERANCE) -> dict:
    found_abv = extract_abv(ocr_text)

    if found_abv is None:
        return {
            "rule": "abv",
            "status": "REVIEW",
            "expected": expected_abv,
            "found": None,
            "reason": "Could not locate an ABV value in OCR text.",
        }

    diff = abs(found_abv - expected_abv)
    status = "PASS" if diff <= tolerance else "FAIL"

    return {
        "rule": "abv",
        "status": status,
        "expected": expected_abv,
        "found": found_abv,
        "difference": round(diff, 3),
        "tolerance": tolerance,
    }

# ---------------------------------------------------------------------------
# Government Warning Rule
# ---------------------------------------------------------------------------

_WARNING_HEADER = "GOVERNMENT WARNING:"


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def check_government_warning(ocr_text: str) -> dict:
    """Warning must contain 'GOVERNMENT WARNING:' in exact ALL CAPS,
    and the full body text must exactly match the canonical warning
    (after whitespace normalization only — no case or punctuation
    forgiveness, per Jenny's requirement).
    """
    if _WARNING_HEADER not in ocr_text:
        return {
            "rule": "government_warning",
            "status": "FAIL",
            "reason": "'GOVERNMENT WARNING:' header not found in exact ALL CAPS.",
        }

    header_index = ocr_text.index(_WARNING_HEADER)
    candidate = ocr_text[header_index:]
    normalized_candidate = _collapse_whitespace(candidate)
    normalized_canonical = _collapse_whitespace(CANONICAL_WARNING)

    if normalized_candidate.startswith(normalized_canonical):
        status = "PASS"
        reason = "Exact match against canonical warning text."
    elif normalized_canonical[:40] in normalized_candidate:
        # Header and opening text present but full body doesn't match
        # exactly — likely an OCR misread rather than a wrong label.
        status = "REVIEW"
        reason = "Header found and text is similar, but not an exact match. Needs agent review."
    else:
        status = "FAIL"
        reason = "Header found but body text does not match canonical warning."

    return {
        "rule": "government_warning",
        "status": status,
        "reason": reason,
    }
