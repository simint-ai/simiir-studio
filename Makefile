.PHONY: install run dev test format lint clean docker-build docker-run help

help:
	@echo "SimIIR API - Available commands:"
	@echo "  make install      - Install dependencies with poetry"
	@echo "  make run          - Run the API server"
	@echo "  make dev          - Run in development mode with auto-reload"
	@echo "  make test         - Run tests"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Lint code with ruff"
	@echo "  make clean        - Clean generated files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"

install:
	poetry install

run:
	poetry run simiir-api

dev:
	poetry run uvicorn simiir_api.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest -v

format:
	poetry run black src/ tests/

lint:
	poetry run ruff check src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.db" -delete
	rm -rf .pytest_cache
	rm -rf dist/ build/ *.egg-info

docker-build:
	docker build -t simiir-api:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

