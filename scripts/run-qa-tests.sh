#!/bin/bash
#
# QA-011: Contract & Visual Regression Test Runner
# Usage: ./scripts/run-qa-tests.sh [contract|visual|all]
#

set -e

PROJECT_DIR="/root/.openclaw/workspace/personal-monitoring-dashboard"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════════════════"
echo "  QA-011: Contract & Visual Regression Test Suite"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running${NC}"
    exit 1
fi

# Function to check if services are healthy
check_services() {
    echo "Checking service health..."
    
    # Check backend
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Backend (localhost:8000)"
    else
        echo -e "  ${RED}✗${NC} Backend not responding"
        return 1
    fi
    
    # Check frontend
    if curl -s http://localhost:8000/ | head -1 | grep -q "DOCTYPE"; then
        echo -e "  ${GREEN}✓${NC} Frontend accessible"
    else
        echo -e "  ${RED}✗${NC} Frontend not accessible"
        return 1
    fi
    
    return 0
}

# Start services via launch.sh (tests the launch script)
start_services() {
    echo ""
    echo "Starting Docker Compose stack via launch.sh..."
    echo "(This tests the launch script as part of regression)"
    cd "$PROJECT_DIR"
    
    # Run launch.sh and capture output
    ./launch.sh
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}ERROR: launch.sh failed with exit code $EXIT_CODE${NC}"
        return 1
    fi
    
    echo "Waiting for services to be healthy..."
    sleep 2
    
    # Wait for backend health
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}Services ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${RED}ERROR: Services failed to become healthy within 60 seconds${NC}"
    return 1
}

# Run contract tests
run_contract_tests() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  QA-CONTRACT: API Contract Tests"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    cd "$PROJECT_DIR/backend"
    source .venv/bin/activate
    
    echo "Running contract tests..."
    pytest tests/test_contract.py -v --tb=short
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ All contract tests passed${NC}"
    else
        echo ""
        echo -e "${RED}✗ Contract tests failed${NC}"
        echo ""
        echo "Defect Reporting Template:"
        echo "  DEF-XXX: [Brief description]"
        echo "  Status: OPEN"
        echo "  Severity: Major"
        echo "  Discovered: $(date +%Y-%m-%d)"
        echo "  Reporter: QA Engineer"
        echo "  Related To: QA-011"
    fi
    
    return $EXIT_CODE
}

# Run visual regression tests
run_visual_tests() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  QA-VISUAL: Visual Regression Tests"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    cd "$PROJECT_DIR"
    
    # Check for playwright
    if ! python -c "import playwright" 2>/dev/null; then
        echo -e "${YELLOW}WARNING: Playwright not installed${NC}"
        echo "Installing..."
        pip install playwright
        playwright install chromium
    fi
    
    echo "Running visual regression tests..."
    echo "Mode: Headless (use --headed for visual debugging)"
    echo ""
    
    pytest e2e/test_visual_regression.py -v --tb=short 2>&1 | tee /tmp/visual-test-output.log || true
    
    EXIT_CODE=${PIPESTATUS[0]}
    
    # Check for baseline creation
    if grep -q "Created baseline" /tmp/visual-test-output.log; then
        echo ""
        echo -e "${YELLOW}! First run detected - baselines created${NC}"
        echo "  Location: e2e/visual-baselines/"
        echo "  Action: Review baselines and re-run tests"
        echo ""
    fi
    
    # Check for failures
    if [ $EXIT_CODE -ne 0 ]; then
        if [ -d "$PROJECT_DIR/e2e/visual-diffs" ] && [ "$(ls -A $PROJECT_DIR/e2e/visual-diffs)" ]; then
            echo -e "${RED}✗ Visual differences detected${NC}"
            echo ""
            echo "Diff files location: e2e/visual-diffs/"
            ls -la "$PROJECT_DIR/e2e/visual-diffs/"
            echo ""
            echo "To review differences:"
            echo "  1. Check .png files in e2e/visual-diffs/"
            echo "  2. If intentional design change:"
            echo "     cp e2e/visual-diffs/*-current.png e2e/visual-baselines/"
            echo "  3. If bug: file DEF-XXX and assign to developer"
        fi
    else
        echo -e "${GREEN}✓ All visual tests passed${NC}"
    fi
    
    return $EXIT_CODE
}

# Run all QA tests
run_all_tests() {
    CONTRACT_FAILED=0
    VISUAL_FAILED=0
    
    run_contract_tests || CONTRACT_FAILED=1
    run_visual_tests || VISUAL_FAILED=1
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  QA-011: Test Summary"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    if [ $CONTRACT_FAILED -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Contract Tests: PASSED"
    else
        echo -e "  ${RED}✗${NC} Contract Tests: FAILED"
    fi
    
    if [ $VISUAL_FAILED -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} Visual Tests: PASSED"
    else
        echo -e "  ${RED}✗${NC} Visual Tests: FAILED"
    fi
    
    echo ""
    
    if [ $CONTRACT_FAILED -eq 0 ] && [ $VISUAL_FAILED -eq 0 ]; then
        echo -e "${GREEN}Overall: QA-011 PASSED${NC}"
        return 0
    else
        echo -e "${RED}Overall: QA-011 FAILED${NC}"
        return 1
    fi
}

# Main
main() {
    cd "$PROJECT_DIR"
    
    # Check services
    if ! check_services; then
        start_services || exit 1
    fi
    
    # Run based on argument
    case "${1:-all}" in
        contract)
            run_contract_tests
            ;;
        visual)
            run_visual_tests
            ;;
        all)
            run_all_tests
            ;;
        *)
            echo "Usage: $0 [contract|visual|all]"
            echo ""
            echo "  contract - Run API contract tests only"
            echo "  visual   - Run visual regression tests only"
            echo "  all      - Run both (default)"
            exit 1
            ;;
    esac
}

main "$@"
