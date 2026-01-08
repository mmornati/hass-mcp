.PHONY: help install install-dev test test-cov lint format type-check security check all clean setup env-check

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync

install-dev: ## Install development dependencies
	uv sync --extra dev

setup: ## Setup development environment (install deps + pre-commit hooks)
	uv sync --extra dev
	uv run pre-commit install
	@echo "✅ Development environment setup complete!"
	@echo ""
	@echo "Quick reference:"
	@echo "  make test          - Run tests"
	@echo "  make format        - Format code"
	@echo "  make lint          - Check code quality"
	@echo "  make pre-commit    - Run all pre-commit hooks"

env-check: ## Check if development environment is properly configured
	@echo "Checking development environment..."
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv is not installed. Install it from https://docs.astral.sh/uv/"; exit 1; }
	@echo "✅ uv is installed: $$(uv --version)"
	@if [ -d ".venv" ]; then \
		echo "✅ Virtual environment exists at .venv"; \
	else \
		echo "⚠️  No virtual environment found. Run 'make setup' to create one."; \
	fi
	@if [ -f ".venv/bin/ruff" ] || uv run which ruff >/dev/null 2>&1; then \
		echo "✅ ruff is available"; \
	else \
		echo "❌ ruff not found. Run 'make install-dev' to install dependencies."; \
		exit 1; \
	fi
	@echo "✅ Environment is properly configured!"


test: ## Run tests
	uv run pytest tests/

test-cov: ## Run tests with coverage
	uv run pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

test-verbose: ## Run tests with verbose output
	uv run pytest tests/ -vv

lint: ## Run linter (ruff check)
	uv run ruff check app/ tests/

lint-fix: ## Run linter and fix issues
	uv run ruff check app/ tests/ --fix

format: ## Format code (ruff format)
	uv run ruff format app/ tests/

format-check: ## Check code formatting without making changes
	uv run ruff format app/ tests/ --check

type-check: ## Run type checker (mypy)
	uv run mypy app/

security: ## Run security scanner (bandit)
	uv run bandit -r app/

check: lint format-check type-check security ## Run all code quality checks

pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

pre-commit-staged: ## Run pre-commit hooks on staged files
	uv run pre-commit run

clean: ## Clean up generated files
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: check test-cov ## Run all checks and tests (full CI simulation)
