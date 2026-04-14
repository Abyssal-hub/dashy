#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "========================================="
echo "QA-REG-001: Backend Foundation Regression"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Function to run a test step
run_step() {
    local step_name="$1"
    shift
    echo ""
    echo "[$step_name] Running: $*"
    if "$@"; then
        echo -e "${GREEN}✓ $step_name PASSED${NC}"
    else
        echo -e "${RED}✗ $step_name FAILED${NC}"
        FAILED=1
    fi
}

# Step 1: Python syntax check
step1_syntax() {
    cd "$BACKEND_DIR"
    .venv/bin/python -m py_compile app/main.py
}

# Step 2: pytest with testcontainers
step2_pytest() {
    cd "$BACKEND_DIR"
    .venv/bin/pytest -v --tb=short 2>&1 | head -100
}

# Step 3: alembic check (syntax only - requires live DB for actual migration)
step3_alembic_check() {
    cd "$BACKEND_DIR"
    .venv/bin/alembic current 2>&1 | grep -E "(Current revision|HEAD)" || true
    # Just verify alembic can load the config
    .venv/bin/python -c "from alembic.config import Config; Config('alembic.ini')"
}

# Step 4: Docker build test
step4_docker_build() {
    cd "$BACKEND_DIR"
    docker build -t dashboard-backend:test . 2>&1 | tail -20
}

# Step 5: App import test
step5_app_import() {
    cd "$BACKEND_DIR"
    .venv/bin/python -c "from app.main import create_app; app = create_app(); print('App creates successfully')"
}

# Step 6: Verify test files exist
step6_test_files() {
    cd "$BACKEND_DIR"
    test -f tests/test_health.py
    test -f tests/test_auth.py
    test -f tests/conftest.py
    echo "All test files present"
}

# Run all steps
run_step "1/6: Python syntax check" step1_syntax
run_step "2/6: Pytest with testcontainers" step2_pytest
run_step "3/6: Alembic config check" step3_alembic_check
run_step "4/6: Docker build" step4_docker_build
run_step "5/6: App import" step5_app_import
run_step "6/6: Test files check" step6_test_files

echo ""
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}QA-REG-001: ALL CHECKS PASSED${NC}"
    echo "========================================="
    exit 0
else
    echo -e "${RED}QA-REG-001: SOME CHECKS FAILED${NC}"
    echo "========================================="
    exit 1
fi
