"""
test_rules.py
Unit tests for app/rules.py. These test the matching logic directly
against synthetic OCR text — no actual image/OCR involved, so tests
run fast and deterministically.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rules import (
    normalize_brand,
    check_brand,
    apply_brand_override,
    extract_abv,
    check_abv,
    check_government_warning,
    CANONICAL_WARNING,
)


# ---------------------------------------------------------------------------
# Brand Name Rule
# ---------------------------------------------------------------------------

def test_normalize_brand_strips_punctuation_and_case():
    assert normalize_brand("Stone's Throw") == "STONES THROW"
    assert normalize_brand("stone throw") == "STONE THROW"


def test_normalize_brand_compresses_whitespace():
    assert normalize_brand("Stone   Throw") == "STONE THROW"


def test_check_brand_exact_match_passes():
    result = check_brand("Stone's Throw", "STONES THROW BREWING CO 12.5% ABV")
    assert result["status"] == "PASS"


def test_check_brand_mismatch_fails():
    result = check_brand("Stone's Throw", "COMPLETELY DIFFERENT BRAND NAME")
    assert result["status"] == "FAIL"


def test_apply_brand_override_forces_pass():
    result = check_brand("Stone's Throw", "COMPLETELY DIFFERENT BRAND NAME")
    assert result["status"] == "FAIL"
    overridden = apply_brand_override(result)
    assert overridden["status"] == "PASS"
    assert overridden["overridden_by_agent"] is True


# ---------------------------------------------------------------------------
# ABV Rule
# ---------------------------------------------------------------------------

def test_extract_abv_percent_before_label():
    assert extract_abv("Net Contents 12 FL OZ  12.5% ALC BY VOL") == 12.5


def test_extract_abv_label_before_percent():
    assert extract_abv("ABV 5.0%") == 5.0


def test_extract_abv_missing_returns_none():
    assert extract_abv("No alcohol content listed here") is None


def test_check_abv_within_tolerance_passes():
    result = check_abv(12.5, "12.5% ALC BY VOL", tolerance=0.1)
    assert result["status"] == "PASS"


def test_check_abv_outside_tolerance_fails():
    result = check_abv(12.5, "11.0% ALC BY VOL", tolerance=0.1)
    assert result["status"] == "FAIL"


def test_check_abv_not_found_is_review():
    result = check_abv(12.5, "no abv info here")
    assert result["status"] == "REVIEW"


# ---------------------------------------------------------------------------
# Government Warning Rule
# ---------------------------------------------------------------------------

def test_warning_exact_match_passes():
    text = f"SOME LABEL TEXT {CANONICAL_WARNING}"
    result = check_government_warning(text)
    assert result["status"] == "PASS"


def test_warning_missing_header_fails():
    result = check_government_warning("Government warning: lowercase header should not count")
    assert result["status"] == "FAIL"


def test_warning_header_present_but_wrong_body_fails():
    text = "GOVERNMENT WARNING: This is not the real warning text at all."
    result = check_government_warning(text)
    assert result["status"] == "FAIL"
