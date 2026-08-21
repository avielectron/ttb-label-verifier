# Approach

## Problem
TTB agents manually check ~150,000 label applications/year against
three recurring fields: brand name, ABV, and the government warning
statement. This prototype automates the first pass of that check so
agents can confirm or override in seconds rather than reading the
whole label by hand.

## Pipeline
1. **Upload** — agent submits a label image plus the expected brand
   and ABV (single check), or a CSV + zip of images (batch check).
2. **Preprocess** (`app/ocr.py`) — downscale, grayscale, deskew,
   CLAHE contrast boost, adaptive threshold. This directly targets
   Jenny's observation that uploaded images often have skew, glare,
   or low lighting.
3. **OCR** — Tesseract via `pytesseract`, entirely local. No image or
   text ever leaves the machine running the app, satisfying Marcus's
   firewall constraint.
4. **Rule evaluation** (`app/rules.py`):
   - **Brand**: normalize (uppercase, strip punctuation, compress
     whitespace) both the expected brand and OCR text, then RapidFuzz
     partial-ratio match. ≥90 PASS, 80–89 REVIEW, <80 FAIL. An
     agent-facing override lets a human force a PASS when they can
     see the brand is correct despite noisy OCR — this is Dave's
     requirement, not a system that guesses when to trust itself.
   - **ABV**: regex extraction nearest an "ABV" / "ALC BY VOL" marker,
     compared numerically within a configurable tolerance (default
     ±0.1%).
   - **Government Warning**: the header "GOVERNMENT WARNING:" must
     appear in exact ALL CAPS, and the following body text must match
     the canonical warning stored in `app/canonical_warning.txt`
     exactly (after whitespace normalization only). This is
     deliberately strict per Jenny's requirement — no case or
     punctuation forgiveness on the legally mandated text.
5. **Result** — PASS/REVIEW/FAIL per rule, returned in under the
   ~5-second target Sarah Chen set as a hard requirement after the
   prior pilot's 30–40 second scans caused it to be abandoned.

## Speed
The 5-second target is met primarily by downscaling large images
before OCR (`app/utils.py`) and keeping preprocessing to a small,
fixed set of OpenCV operations rather than anything iterative or
model-based. Every OCR call is timed and the timing is surfaced back
to the agent, per the non-functional timing-metrics requirement.

## What this prototype deliberately does not do
- No persistence of images, CSVs, or results — nothing is written to
  disk beyond the process's own memory during a request.
- No outbound network calls of any kind — OCR is 100% local Tesseract.
- No integration with COLA or any TTB internal system.
- No ML-based OCR or cloud vision APIs.
