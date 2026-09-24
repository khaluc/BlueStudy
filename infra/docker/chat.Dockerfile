FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps apps
COPY packages packages
RUN useradd --uid 10001 --create-home padayon
USER padayon
EXPOSE 8001
CMD ["uvicorn", "apps.chat.main:app", "--host", "0.0.0.0", "--port", "8001"]
