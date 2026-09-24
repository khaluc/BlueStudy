FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt requirements-backend.txt ./
RUN pip install --no-cache-dir -r requirements-backend.txt
COPY apps apps
COPY packages packages
COPY scripts scripts
COPY alembic.ini .
RUN useradd --uid 10001 --create-home padayon && mkdir -p /app/data/uploads && chown -R padayon:padayon /app/data
USER padayon
EXPOSE 8000
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
