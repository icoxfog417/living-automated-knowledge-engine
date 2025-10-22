.PHONY: test test-verbose test-cov lint lint-fix format format-check help

help:
	@echo "Available targets:"
	@echo "  test         - Run all tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-cov     - Run tests with coverage report"
	@echo "  lint         - Run ruff linter"
	@echo "  lint-fix     - Run ruff linter with auto-fix"
	@echo "  format       - Format code with ruff"
	@echo "  format-check - Check code formatting"

test:
	uv run pytest

test-verbose:
	uv run pytest -v

test-cov:
	uv run pytest --cov=src --cov-report=term-missing

lint:
	uv run ruff check src tests

lint-fix:
	uv run ruff check --fix src tests

format:
	uv run ruff format src tests

format-check:
	uv run ruff format --check src tests
