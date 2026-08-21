# Testing

## Unit tests
`tests/test_rules.py` covers the three rule functions directly against
synthetic OCR text (no image/Tesseract dependency), so they run fast
and don't require Tesseract to be installed locally.

Run with:
```
pip install -r requirements.txt
pip install pytest
pytest tests/
```

Covered cases:
- Brand: normalization, exact-ish match PASS, mismatch FAIL, agent
  override forcing PASS.
- ABV: extraction with percent-before and percent-after label
  placement, missing-value REVIEW, within/outside tolerance PASS/FAIL.
- Government Warning: exact match PASS, missing header FAIL, header
  present with wrong body FAIL.

## Manual / end-to-end testing
OCR and image preprocessing (`app/ocr.py`) are not unit tested here
since they depend on the Tesseract binary being installed on the
host, which isn't guaranteed in every dev environment. To test the
full pipeline manually:

1. Install Tesseract locally (`apt-get install tesseract-ocr` on
   Ubuntu/Debian, or the equivalent for your OS).
2. `pip install -r requirements.txt`
3. `bash deploy/start.sh` (or `uvicorn app.server:app --reload`)
4. Open `http://localhost:8000`, upload a real label photo, and
   confirm results return in roughly 5 seconds or less.

## Batch testing
`tests/sample_applications.csv` is provided as a template for the
batch CSV format. Place matching images in `tests/sample_images/`
(populate this folder with your own label photos — it ships empty),
zip them, and upload both files through the batch panel to confirm
the downloaded results CSV has one row per input row with
brand/ABV/warning statuses populated.

## Known gaps (prototype scope)
- No automated test currently exercises the FastAPI endpoints
  themselves (`app/server.py`) or the OCR pipeline end-to-end, since
  both require either a running Tesseract binary or sample label
  images that weren't provided with the spec. Recommend adding these
  once real sample labels are available.
