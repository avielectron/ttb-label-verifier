"""
server.py
FastAPI application entry point. Serves the single-page UI and two
endpoints:
  - POST /api/verify        single label image verification
  - POST /api/batch         zip + CSV batch verification

No persistence: uploaded files are processed in-memory per request
and discarded, per the "no sensitive data stored" requirement.
"""

import os

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import io

from app.ocr import extract_text
from app.rules import check_brand, check_abv, check_government_warning
from app.batch import run_batch, results_to_csv_bytes
from app.utils import read_image_bytes

app = FastAPI(title="TTB Label Verifier (Prototype)")

_WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")

app.mount("/static", StaticFiles(directory=_WEB_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = os.path.join(_WEB_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/verify")
async def verify_single(
    brand: str = Form(...),
    abv: float = Form(...),
    image: UploadFile = File(...),
):
    raw_bytes = await image.read()

    try:
        cv_image = read_image_bytes(raw_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ocr_text, elapsed = extract_text(cv_image)

    brand_result = check_brand(brand, ocr_text)
    abv_result = check_abv(abv, ocr_text)
    warning_result = check_government_warning(ocr_text)

    return {
        "ocr_seconds": round(elapsed, 2),
        "brand": brand_result,
        "abv": abv_result,
        "government_warning": warning_result,
        "raw_ocr_text": ocr_text,
    }


@app.post("/api/batch")
async def verify_batch(
    csv_file: UploadFile = File(...),
    zip_file: UploadFile = File(...),
):
    csv_bytes = await csv_file.read()
    zip_bytes = await zip_file.read()

    try:
        results_df = run_batch(csv_bytes, zip_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    csv_output = results_to_csv_bytes(results_df)

    return StreamingResponse(
        io.BytesIO(csv_output),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=batch_results.csv"},
    )
