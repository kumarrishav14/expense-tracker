#!/bin/bash

# Database Sanity Test Runner
# Run this script whenever making changes to database-related code

set -e  # Exit on any error

echo "🔍 Database Sanity Test Suite"
echo "============================"
echo "Running critical database tests to validate core functionality..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to the project root directory
cd "$(dirname "$0")/../.."

echo -e "${BLUE}📁 Working Directory:${NC} $(pwd)"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment active:${NC} $VIRTUAL_ENV"
else
    echo -e "${YELLOW}⚠️  No virtual environment detected. Consider activating .venv${NC}"
fi
echo ""

# Run sanity tests with different verbosity options
echo -e "${BLUE}🧪 Running Database Sanity Tests...${NC}"
echo ""

# Option 1: Quick run (default)
if [[ "$1" == "--quick" || "$1" == "-q" ]]; then
    echo "Running in QUICK mode (minimal output)..."
    python -m pytest -m sanity tests/db_tests/ --tb=short -q

# Option 2: Verbose run
elif [[ "$1" == "--verbose" || "$1" == "-v" ]]; then
    echo "Running in VERBOSE mode (detailed output)..."
    python -m pytest -m sanity tests/db_tests/ -v -s

# Option 3: Coverage run
elif [[ "$1" == "--coverage" || "$1" == "-c" ]]; then
    echo "Running with COVERAGE analysis..."
    python -m pytest -m sanity tests/db_tests/ --cov=core.database --cov-report=term-missing

# Option 4: Fail fast mode
elif [[ "$1" == "--fail-fast" || "$1" == "-x" ]]; then
    echo "Running in FAIL-FAST mode (stop on first failure)..."
    python -m pytest -m sanity tests/db_tests/ -x --tb=short

# Default: Standard run
else
    echo "Running in STANDARD mode..."
    echo "Use --quick, --verbose, --coverage, or --fail-fast for different modes"
    echo ""
    python -m pytest -m sanity tests/db_tests/ --tb=short
fi

# Check exit code
if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ ALL SANITY TESTS PASSED!${NC}"
    echo -e "${GREEN}🎉 Database changes are safe to proceed.${NC}"
    echo ""
    echo -e "${BLUE}📋 Tests Validated:${NC}"
    echo "   • Basic CRUD operations (categories, transactions, accounts)"
    echo "   • Atomic rollback behavior (critical for data integrity)"
    echo "   • Return type compliance (OperationResult/BatchOperationResult)"
    echo "   • End-to-end workflow functionality"
    echo "   • Large batch processing safety"
    echo "   • Error handling and validation"
else
    echo ""
    echo -e "${RED}❌ SANITY TESTS FAILED!${NC}"
    echo -e "${RED}🚨 DO NOT PROCEED with database changes until tests pass.${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Debug Tips:${NC}"
    echo "   • Run with --verbose for detailed output"
    echo "   • Check database schema migrations"
    echo "   • Verify atomic transaction behavior"
    echo "   • Review return type changes"
    echo ""
    exit 1
fi

echo ""
echo -e "${BLUE}📚 Usage Examples:${NC}"
echo "   ./tests/db_tests/run_sanity_tests.sh          # Standard run"
echo "   ./tests/db_tests/run_sanity_tests.sh --quick   # Quick validation"
echo "   ./tests/db_tests/run_sanity_tests.sh --verbose # Detailed output"
echo "   ./tests/db_tests/run_sanity_tests.sh --coverage # With coverage"
echo ""
echo -e "${BLUE}🎯 What These Tests Validate:${NC}"
echo "   • Data integrity and atomic operations"
echo "   • API contract compliance"
echo "   • Core database functionality"
echo "   • Error handling and rollback behavior"
echo ""
