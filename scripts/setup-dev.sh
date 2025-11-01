#!/bin/bash
# Setup development environment for hass-mcp

set -e

echo "🚀 Setting up hass-mcp development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "📦 Install it from: https://github.com/astral-sh/uv"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync --extra dev

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
uv run pre-commit install

echo "✅ Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Run tests: uv run pytest tests/"
echo "  2. Check code quality: uv run pre-commit run --all-files"
echo "  3. Format code: uv run ruff format app/ tests/"
echo "  4. Type check: uv run mypy app/"
echo ""

