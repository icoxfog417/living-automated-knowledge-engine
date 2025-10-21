.PHONY: test test-verbose test-cov help

help:
	@echo "Available targets:"
	@echo "  test         - Run all tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-cov     - Run tests with coverage report"

test:
	uv run pytest

test-verbose:
	uv run pytest -v

test-cov:
	uv run pytest --cov=src --cov-report=term-missing
