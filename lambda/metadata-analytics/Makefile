.PHONY: install test lint format clean

install:
	uv sync

test:
	uv run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	uv run ruff check src/ tests/
	uv run black --check src/ tests/

format:
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

clean:
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
