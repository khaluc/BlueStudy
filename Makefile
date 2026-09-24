.PHONY: install test chat benchmark backend
install:
	python -m pip install -r requirements-dev.txt
test:
	python -m pytest -q
chat:
	python -m uvicorn apps.chat.main:app --host 127.0.0.1 --port 8001
benchmark:
	python -m scripts.benchmark_llm
backend:
	docker compose up --build -d
