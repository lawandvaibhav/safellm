#!/bin/bash
# Local CI Check Runner for Unix/Linux/macOS
# This script runs all CI checks locally

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to print headers
print_header() {
    echo -e "\n${BOLD}${BLUE}============================================================${NC}"
    echo -e "${BOLD}${BLUE}$(printf '%*s' $(((60+${#1})/2)) "$1")${NC}"
    echo -e "${BOLD}${BLUE}============================================================${NC}"
}

# Function to print steps
print_step() {
    echo -e "\n${BOLD}${CYAN}🔍 $1${NC}"
}

# Function to run a command with timing
run_check() {
    local description="$1"
    shift
    local cmd="$@"
    
    echo -e "${YELLOW}Running: $cmd${NC}"
    start_time=$(date +%s)
    
    if eval "$cmd"; then
        end_time=$(date +%s)
        elapsed=$((end_time - start_time))
        echo -e "${GREEN}✅ $description passed (${elapsed}s)${NC}"
        return 0
    else
        end_time=$(date +%s)
        elapsed=$((end_time - start_time))
        echo -e "${RED}❌ $description failed (${elapsed}s)${NC}"
        return 1
    fi
}

# Parse arguments
FAST=false
SKIP_CHECKS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST=true
            shift
            ;;
        --skip)
            SKIP_CHECKS="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--fast] [--skip CHECKS]"
            echo ""
            echo "Options:"
            echo "  --fast          Skip slower checks (mypy, pytest)"
            echo "  --skip CHECKS   Comma-separated list of checks to skip"
            echo "                 Available: ruff,black,mypy,bandit,pytest,build"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --fast"
            echo "  $0 --skip mypy,bandit"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Convert skip list to array
IFS=',' read -ra SKIP_ARRAY <<< "$SKIP_CHECKS"

# Function to check if we should skip a check
should_skip() {
    local check="$1"
    
    # Check --fast flag
    if [ "$FAST" = true ] && [[ "$check" == "mypy" || "$check" == "pytest" ]]; then
        return 0
    fi
    
    # Check --skip list
    for skip in "${SKIP_ARRAY[@]}"; do
        if [ "$check" = "$skip" ]; then
            return 0
        fi
    done
    
    return 1
}

# Find project root (script is in scripts/ subdirectory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Validate project structure
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found in $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"

# Track failures
FAILED_CHECKS=()
TOTAL_START=$(date +%s)

print_header "LOCAL CI CHECKS"
echo -e "${PURPLE}Project: $PROJECT_ROOT${NC}"
echo -e "${PURPLE}Python: $(which python)${NC}"

if [ -n "$SKIP_CHECKS" ] || [ "$FAST" = true ]; then
    skip_list=""
    if [ "$FAST" = true ]; then
        skip_list="mypy,pytest"
    fi
    if [ -n "$SKIP_CHECKS" ]; then
        if [ -n "$skip_list" ]; then
            skip_list="$skip_list,$SKIP_CHECKS"
        else
            skip_list="$SKIP_CHECKS"
        fi
    fi
    echo -e "${YELLOW}Skipping: $skip_list${NC}"
fi

# Run checks
if ! should_skip "ruff"; then
    print_step "Linting with ruff"
    if ! run_check "Ruff linting" "ruff check src/ tests/"; then
        FAILED_CHECKS+=("ruff")
    fi
else
    echo -e "\n${YELLOW}⏭️  Skipping ruff${NC}"
fi

if ! should_skip "black"; then
    print_step "Checking formatting with black"
    if ! run_check "Black formatting" "black --check src/ tests/"; then
        FAILED_CHECKS+=("black")
    fi
else
    echo -e "\n${YELLOW}⏭️  Skipping black${NC}"
fi

if ! should_skip "mypy"; then
    print_step "Type checking with mypy"
    if ! run_check "MyPy type checking" "mypy src/safellm"; then
        FAILED_CHECKS+=("mypy")
    fi
else
    echo -e "\n${YELLOW}⏭️  Skipping mypy${NC}"
fi

if ! should_skip "bandit"; then
    print_step "Security checking with bandit"
    if ! run_check "Bandit security check" "bandit -r src/safellm"; then
        FAILED_CHECKS+=("bandit")
    fi
else
    echo -e "\n${YELLOW}⏭️  Skipping bandit${NC}"
fi

if ! should_skip "pytest"; then
    print_step "Running tests with pytest"
    if ! run_check "Pytest tests with coverage" "pytest --cov=safellm --cov-report=term-missing --cov-report=html"; then
        FAILED_CHECKS+=("pytest")
    fi
else
    echo -e "\n${YELLOW}⏭️  Skipping pytest${NC}"
fi

if ! should_skip "build"; then
    print_step "Building package"
    
    # Install build tool if needed
    if ! python -m build --help >/dev/null 2>&1; then
        echo -e "${YELLOW}Installing build tool...${NC}"
        if ! run_check "Install build tool" "pip install build"; then
            FAILED_CHECKS+=("build-install")
        fi
    fi
    
    if ! run_check "Package build" "python -m build"; then
        FAILED_CHECKS+=("build")
    else
        print_step "Testing built package"
        if ! run_check "Built package test" "python -c \"import safellm; print(f'SafeLLM version: {safellm.__version__}')\""; then
            FAILED_CHECKS+=("build-test")
        fi
    fi
else
    echo -e "\n${YELLOW}⏭️  Skipping build${NC}"
fi

# Summary
TOTAL_END=$(date +%s)
TOTAL_TIME=$((TOTAL_END - TOTAL_START))

print_header "CI CHECKS SUMMARY"

if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 All checks passed! 🎉${NC}"
    echo -e "${GREEN}Total time: ${TOTAL_TIME}s${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}❌ ${#FAILED_CHECKS[@]} check(s) failed:${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo -e "${RED}  • $check${NC}"
    done
    echo -e "${YELLOW}Total time: ${TOTAL_TIME}s${NC}"
    echo -e "\n${YELLOW}💡 Fix the issues above and run again${NC}"
    exit 1
fi
