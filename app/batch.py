"""
batch.py
Batch verification: takes a zip of label images plus a CSV of
expected fields (product_id,brand,abv,filename) and produces a
results CSV with PASS/FAIL/REVIEW per rule for each row.
"""

import io
import zipfile

import pandas as pd

from app.ocr import extract_text
from app.rules import check_brand, check_abv, check_government_warning
from app.utils import read_image_bytes

REQUIRED_CSV_COLUMNS = ["product_id", "brand", "abv", "filename"]


def _load_zip_images(zip_bytes: bytes) -> dict:
    """Return {filename: raw_bytes} for every file in the zip."""
    images = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            images[name] = zf.read(name)
    return images


def _process_row(row: pd.Series, images: dict) -> dict:
    product_id = row["product_id"]
    brand = str(row["brand"])
    abv = float(row["abv"])
    filename = str(row["filename"])

    result = {
        "product_id": product_id,
        "filename": filename,
        "brand_status": "FAIL",
        "brand_score": None,
        "abv_status": "FAIL",
        "abv_found": None,
        "warning_status": "FAIL",
        "warning_reason": "",
        "ocr_seconds": None,
        "error": "",
    }

    raw_bytes = images.get(filename)
    if raw_bytes is None:
        result["error"] = f"Image '{filename}' not found in zip."
        return result

    try:
        image = read_image_bytes(raw_bytes)
        ocr_text, elapsed = extract_text(image)
        result["ocr_seconds"] = round(elapsed, 2)
    except Exception as exc:  # noqa: BLE001 - surfaced to the CSV, not swallowed
        result["error"] = f"OCR failed: {exc}"
        return result

    brand_result = check_brand(brand, ocr_text)
    abv_result = check_abv(abv, ocr_text)
    warning_result = check_government_warning(ocr_text)

    result["brand_status"] = brand_result["status"]
    result["brand_score"] = brand_result["score"]
    result["abv_status"] = abv_result["status"]
    result["abv_found"] = abv_result.get("found")
    result["warning_status"] = warning_result["status"]
    result["warning_reason"] = warning_result.get("reason", "")

    return result


def run_batch(csv_bytes: bytes, zip_bytes: bytes) -> pd.DataFrame:
    """Run verification over every row in the CSV and return a
    results DataFrame ready to be written out as a downloadable CSV.
    """
    df = pd.read_csv(io.BytesIO(csv_bytes))

    missing_columns = [c for c in REQUIRED_CSV_COLUMNS if c not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {missing_columns}")

    images = _load_zip_images(zip_bytes)

    rows = [_process_row(row, images) for _, row in df.iterrows()]
    return pd.DataFrame(rows)


def results_to_csv_bytes(results_df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    results_df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
