# TTB Label Verifier (Prototype)

A standalone FastAPI application that checks a label image against
expected Brand Name, ABV, and Government Warning text, using
entirely local OCR (Tesseract). This is a feasibility prototype only
— it does not integrate with COLA or any TTB internal system, and it
stores nothing.

## Features
- **Single label check** — upload one image + brand + ABV, get
  PASS/REVIEW/FAIL per rule in ~5 seconds or less.
- **Batch check** — upload a CSV (`product_id,brand,abv,filename`)
  and a zip of matching images, download a results CSV.
- **100% local processing** — OpenCV preprocessing + Tesseract OCR,
  no outbound network calls, nothing written to disk.
- **Agent override** — brand rule can be manually marked PASS by the
  reviewing agent when they judge OCR/fuzzy-matching got it wrong.

## Quick start (local)
```bash
# Tesseract must be installed on the host first, e.g.:
#   sudo apt-get update && sudo apt-get install -y tesseract-ocr

pip install -r requirements.txt
bash deploy/start.sh
# App is served at http://localhost:8000
```

## Repository layout
```
ttb-label-verifier/
├─ app/            FastAPI backend, OCR, rules, batch processing
├─ web/            Single-page frontend (HTML/CSS/JS, no build step)
├─ tests/          Unit tests + sample batch CSV/images
├─ docs/           Approach, assumptions, testing notes
└─ deploy/         Render.com start script + deployment guide
```

## Rules implemented
| Rule | Logic | Thresholds |
|---|---|---|
| Brand Name | RapidFuzz partial-ratio match, normalized (uppercase, no punctuation, single-spaced) | ≥90 PASS, 80–89 REVIEW, <80 FAIL |
| ABV | Regex-extracted from OCR text near an ABV/ALC BY VOL marker, compared numerically | ±0.1% tolerance (default) |
| Government Warning | "GOVERNMENT WARNING:" must appear in exact ALL CAPS; body must match `app/canonical_warning.txt` exactly | Exact match required |

See `docs/approach.md` for the full pipeline and `docs/assumptions.md`
for anything the spec left implicit.

## Deployment
See `deploy/render-deploy.md` for step-by-step Render.com free-tier
deployment instructions, including the required Tesseract `apt-get`
install step.

## Status
Prototype for internal demonstration. Not production-ready, not
connected to any live TTB system.
