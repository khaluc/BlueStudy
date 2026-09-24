FROM python:3.14-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-vie fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-backend.txt ./
RUN pip install --no-cache-dir -r requirements-backend.txt
COPY apps apps
COPY packages packages
RUN useradd --uid 10001 --create-home padayon
USER padayon
CMD ["python", "-m", "apps.worker.main"]
