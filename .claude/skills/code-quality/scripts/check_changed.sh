#!/bin/bash
# Beautiful Code - Monorepo-aware linting for changed files
# Usage: ./check_changed.sh
# Environment: EMERGENCY_BYPASS=true to skip checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Beautiful Code - Checking changed files...${NC}"

# Get changed files (staged + unstaged)
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || git diff --name-only)

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${GREEN}No changed files to check.${NC}"
    exit 0
fi

# Emergency bypass check
if [ "$EMERGENCY_BYPASS" = "true" ]; then
    echo -e "${YELLOW}EMERGENCY BYPASS ACTIVE - logging and skipping checks${NC}"
    echo "$(date) - $USER - BYPASS - $(git rev-parse --short HEAD 2>/dev/null || echo 'no-commit')" >> .lint-bypass-audit.log
    exit 0
fi

# Find project root for a given file (monorepo support)
find_project_root() {
    local file="$1"
    local dir=$(dirname "$file")

    while [ "$dir" != "." ] && [ "$dir" != "/" ]; do
        # Check for project markers
        if [ -f "$dir/package.json" ] || [ -f "$dir/go.mod" ] || \
           [ -f "$dir/pyproject.toml" ] || [ -f "$dir/Cargo.toml" ]; then
            echo "$dir"
            return
        fi
        dir=$(dirname "$dir")
    done
    echo "."
}

# Track exit codes
FAILED=0

# Group files by project root
declare -A TS_PROJECTS
declare -A PY_PROJECTS
declare -A GO_PROJECTS
declare -A RS_PROJECTS

for file in $CHANGED_FILES; do
    # Skip if file doesn't exist (deleted)
    [ ! -f "$file" ] && continue

    root=$(find_project_root "$file")

    case "$file" in
        *.ts|*.tsx|*.js|*.jsx)
            TS_PROJECTS["$root"]+="$file "
            ;;
        *.py)
            PY_PROJECTS["$root"]+="$file "
            ;;
        *.go)
            GO_PROJECTS["$root"]+="$file "
            ;;
        *.rs)
            RS_PROJECTS["$root"]+="$file "
            ;;
    esac
done

# Lint TypeScript projects
for root in "${!TS_PROJECTS[@]}"; do
    if [ -f "$root/package.json" ]; then
        echo -e "\n${BLUE}=== TypeScript [$root] ===${NC}"
        files="${TS_PROJECTS[$root]}"

        # Check if ESLint is available
        if [ -f "$root/node_modules/.bin/eslint" ]; then
            (cd "$root" && echo "$files" | xargs npx eslint --fix --max-warnings=0) || FAILED=1
        else
            echo -e "${YELLOW}ESLint not installed in $root, skipping...${NC}"
        fi
    fi
done

# Lint Python projects
for root in "${!PY_PROJECTS[@]}"; do
    if [ -f "$root/pyproject.toml" ] || [ -f "$root/setup.py" ]; then
        echo -e "\n${BLUE}=== Python [$root] ===${NC}"
        files="${PY_PROJECTS[$root]}"

        # Check if ruff is available
        if command -v ruff &> /dev/null; then
            (cd "$root" && echo "$files" | xargs ruff check --fix) || FAILED=1
            (cd "$root" && echo "$files" | xargs ruff format) || true
        else
            echo -e "${YELLOW}Ruff not installed, skipping...${NC}"
        fi

        # Check if mypy is available
        if command -v mypy &> /dev/null; then
            (cd "$root" && echo "$files" | xargs mypy --ignore-missing-imports) || FAILED=1
        fi
    fi
done

# Lint Go projects
for root in "${!GO_PROJECTS[@]}"; do
    if [ -f "$root/go.mod" ]; then
        echo -e "\n${BLUE}=== Go [$root] ===${NC}"

        # Check if golangci-lint is available
        if command -v golangci-lint &> /dev/null; then
            (cd "$root" && golangci-lint run --new-from-rev=HEAD~1 --fix) || FAILED=1
        else
            echo -e "${YELLOW}golangci-lint not installed, skipping...${NC}"
        fi
    fi
done

# Lint Rust projects
for root in "${!RS_PROJECTS[@]}"; do
    if [ -f "$root/Cargo.toml" ]; then
        echo -e "\n${BLUE}=== Rust [$root] ===${NC}"

        (cd "$root" && cargo fmt --all -- --check) || FAILED=1
        (cd "$root" && cargo clippy --all-targets --all-features -- -D warnings) || FAILED=1
    fi
done

# Summary
echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi