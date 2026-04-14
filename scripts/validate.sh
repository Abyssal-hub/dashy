#!/bin/bash
# validation script - run before every push to catch errors early

set -e

echo "========================================"
echo "Local Validation - Pre-Push Check"
echo "========================================"
echo ""

cd "$(dirname "$0")/../backend"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run: python -m venv .venv && source .venv/bin/activate"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo "Step 1: Import smoke test (2 sec)"
echo "------------------------------------"
python -c "from app.main import create_app; print('✓ Imports work')" || {
    echo "❌ Import failed - fix before pushing"
    exit 1
}

echo ""
echo "Step 2: Fast tests (no Docker required, 30 sec)"
echo "------------------------------------------------"
pytest tests/test_auth.py::test_password_hashing tests/test_auth.py::test_create_access_token tests/test_auth.py::test_hash_token -v --tb=short || {
    echo "❌ Fast tests failed"
    exit 1
}

echo ""
echo "Step 3: Full test suite with testcontainers (3 min)"
echo "----------------------------------------------------"
echo "Starting PostgreSQL and Redis containers..."
pytest tests/ -v --tb=short || {
    echo ""
    echo "❌ Full test suite failed"
    echo "Fix errors before pushing to GitHub"
    exit 1
}

echo ""
echo "========================================"
echo "✅ All checks passed - safe to push"
echo "========================================"
