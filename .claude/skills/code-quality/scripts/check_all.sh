#!/bin/bash
# Beautiful Code - Full repository check
# Usage: ./check_all.sh [--fix]
# Flags: --fix to auto-fix issues where possible

set -e

FIX_MODE=false
if [ "$1" = "--fix" ]; then
    FIX_MODE=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Beautiful Code - Full Repository Check${NC}"
echo -e "${BLUE}Fix mode: $FIX_MODE${NC}"
echo ""

FAILED=0

# ============================================
# Secrets Detection
# ============================================
echo -e "${BLUE}=== Secrets Detection ===${NC}"
if command -v gitleaks &> /dev/null; then
    gitleaks detect --verbose || FAILED=1
else
    echo -e "${YELLOW}gitleaks not installed, skipping secrets check${NC}"
fi

# ============================================
# TypeScript
# ============================================
if [ -f "package.json" ]; then
    echo -e "\n${BLUE}=== TypeScript ===${NC}"

    if [ -f "node_modules/.bin/eslint" ]; then
        if [ "$FIX_MODE" = true ]; then
            npx eslint . --ext .ts,.tsx,.js,.jsx --fix --max-warnings=0 || FAILED=1
        else
            npx eslint . --ext .ts,.tsx,.js,.jsx --max-warnings=0 || FAILED=1
        fi
    fi

    if [ -f "tsconfig.json" ]; then
        echo -e "${BLUE}Type checking...${NC}"
        npx tsc --noEmit || FAILED=1
    fi

    # Dependency audit
    echo -e "${BLUE}Checking dependencies...${NC}"
    npm audit --audit-level=high || FAILED=1
fi

# ============================================
# Python
# ============================================
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    echo -e "\n${BLUE}=== Python ===${NC}"

    if command -v ruff &> /dev/null; then
        if [ "$FIX_MODE" = true ]; then
            ruff check . --fix || FAILED=1
            ruff format . || true
        else
            ruff check . || FAILED=1
            ruff format --check . || FAILED=1
        fi
    fi

    if command -v mypy &> /dev/null; then
        echo -e "${BLUE}Type checking...${NC}"
        mypy . --strict --ignore-missing-imports || FAILED=1
    fi

    # Dependency audit
    if command -v pip-audit &> /dev/null; then
        echo -e "${BLUE}Checking dependencies...${NC}"
        pip-audit --strict || FAILED=1
    fi
fi

# ============================================
# Go
# ============================================
if [ -f "go.mod" ]; then
    echo -e "\n${BLUE}=== Go ===${NC}"

    if command -v golangci-lint &> /dev/null; then
        if [ "$FIX_MODE" = true ]; then
            golangci-lint run --fix || FAILED=1
        else
            golangci-lint run || FAILED=1
        fi
    fi

    # Race detection (only without fix mode, as it runs tests)
    if [ "$FIX_MODE" = false ]; then
        echo -e "${BLUE}Running tests with race detector...${NC}"
        go test -race ./... || FAILED=1
    fi

    # Dependency audit
    if command -v govulncheck &> /dev/null; then
        echo -e "${BLUE}Checking dependencies...${NC}"
        govulncheck ./... || FAILED=1
    fi
fi

# ============================================
# Rust
# ============================================
if [ -f "Cargo.toml" ]; then
    echo -e "\n${BLUE}=== Rust ===${NC}"

    if [ "$FIX_MODE" = true ]; then
        cargo fmt --all || FAILED=1
    else
        cargo fmt --all -- --check || FAILED=1
    fi

    cargo clippy --all-targets --all-features -- -D warnings || FAILED=1

    # Dependency audit
    if command -v cargo-audit &> /dev/null; then
        echo -e "${BLUE}Checking dependencies...${NC}"
        cargo audit || FAILED=1
    fi
fi

# ============================================
# Summary
# ============================================
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi