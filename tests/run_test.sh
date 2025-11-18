#!/bin/bash
# Run all tests for luainstaller

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running luainstaller tests..."
echo "=============================="

# Run pytest with coverage
pytest -v --cov=../luainstaller/source --cov-report=term-missing --cov-report=html

echo ""
echo "Tests completed!"
echo "Coverage report generated in htmlcov/index.html"