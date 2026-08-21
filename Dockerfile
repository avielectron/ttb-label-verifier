# Dockerfile
FROM python:3.11-slim

# Install system packages — tesseract for OCR + OpenCV runtime libs
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       tesseract-ocr \
       libgl1 \
       libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Render provides $PORT at runtime; start.sh reads it and launches uvicorn
CMD ["bash", "deploy/start.sh"]
