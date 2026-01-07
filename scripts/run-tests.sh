#!/bin/bash
# MobileDroid Test Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
PARALLEL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            shift
            ;;
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --parallel|-p)
            PARALLEL=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit         Run only unit tests"
            echo "  --integration  Run only integration tests"
            echo "  --e2e          Run only end-to-end tests"
            echo "  --all          Run all tests (default)"
            echo "  --coverage     Generate coverage report"
            echo "  --verbose,-v   Verbose output"
            echo "  --parallel,-p  Run tests in parallel"
            echo "  --help,-h      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Navigate to API directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$SCRIPT_DIR/../packages/api"
cd "$API_DIR"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}       MobileDroid Test Runner             ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -q -r requirements-test.txt

# Build pytest command
PYTEST_CMD="pytest"

# Add test type filter
case $TEST_TYPE in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD tests/unit"
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD tests/integration"
        ;;
    e2e)
        echo -e "${GREEN}Running end-to-end tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD tests/e2e"
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        PYTEST_CMD="$PYTEST_CMD tests/"
        ;;
esac

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=html --cov-report=term-missing"
fi

# Add verbose output
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Run tests
echo ""
echo -e "${BLUE}Executing: $PYTEST_CMD${NC}"
echo ""

$PYTEST_CMD

# Check exit code
TEST_RESULT=$?

echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}       All tests passed!                    ${NC}"
    echo -e "${GREEN}============================================${NC}"
else
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}       Some tests failed!                   ${NC}"
    echo -e "${RED}============================================${NC}"
fi

# Show coverage report location if generated
if [ "$COVERAGE" = true ] && [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo -e "${YELLOW}Coverage report available at: htmlcov/index.html${NC}"
fi

exit $TEST_RESULT
