# Deploying to Render.com (Free Tier)

## 1. Create a new Web Service
- Connect this repository to Render.
- Environment: **Python 3**.

## 2. Build Command
```
apt-get update && apt-get install -y tesseract-ocr && pip install -r requirements.txt
```
Render's build environment is Ubuntu-based, so Tesseract must be
installed via `apt-get` before Python dependencies — the `pytesseract`
package is only a wrapper and does not bundle the Tesseract binary
itself.

## 3. Start Command
```
bash deploy/start.sh
```

## 4. Environment
- No environment variables are required for the prototype.
- No database, no persistent disk, no outbound network calls.

## 5. Free Tier Notes
- Free-tier services spin down after inactivity; the first request
  after idling will be slower than the ~5 second target while the
  instance cold-starts. This is a Render platform characteristic,
  not an application issue.
- Uploaded images and CSVs are processed in memory per-request and
  are never written to disk, so there is nothing to clean up between
  deploys or restarts.

## 6. Verifying the Deploy
Once live, open the Render-provided URL — it serves the single-page
UI directly at `/`. Use the sample CSV and a few label images from
`tests/sample_images/` to confirm the batch flow end-to-end.
