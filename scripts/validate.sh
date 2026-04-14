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
echo "Step 4: Alembic migration check (30 sec)"
echo "------------------------------------------"
echo "Testing migration chain: upgrade → current → downgrade → upgrade"

# Use testcontainers PostgreSQL for alembic check
python -c "
import asyncio
from testcontainers.postgres import PostgresContainer
import subprocess
import os

async def run_alembic_check():
    with PostgresContainer('postgres:15') as postgres:
        db_url = postgres.get_connection_url().replace('postgresql://', 'postgresql+asyncpg://')
        env = os.environ.copy()
        env['DATABASE_URL'] = db_url
        
        # Upgrade head
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print('❌ alembic upgrade head failed:')
            print(result.stderr)
            return False
        print('✓ alembic upgrade head')
        
        # Current
        result = subprocess.run(['alembic', 'current'], capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print('❌ alembic current failed')
            return False
        print('✓ alembic current')
        
        # Downgrade base
        result = subprocess.run(['alembic', 'downgrade', 'base'], capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print('❌ alembic downgrade base failed:')
            print(result.stderr)
            return False
        print('✓ alembic downgrade base')
        
        # Upgrade head again
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True, env=env)
        if result.returncode != 0:
            print('❌ alembic upgrade head (second) failed')
            return False
        print('✓ alembic upgrade head (idempotent)')
        
        return True

success = asyncio.run(run_alembic_check())
exit(0 if success else 1)
" || {
    echo ""
    echo "❌ Alembic migration check failed"
    echo "Fix migration issues before pushing"
    exit 1
}

echo ""
echo "========================================"
echo "✅ All checks passed - safe to push"
echo "========================================"
