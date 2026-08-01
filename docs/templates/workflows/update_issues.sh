#!/usr/bin/env bash

set -euo pipefail

# ============================================================
# ATRIUM ecosystem maintenance script
#
# For every repository:
#   1. Refresh open GitHub issues into agent_dev_logs/issues
#   2. Run pre-commit over all files
#   3. If pre-commit modifies files, rerun it once
#   4. Report the final status
# ============================================================

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

BASE_DIR="${BASE_DIR:-$HOME/PycharmProjects/alto}"
GITHUB_ORG="ufal"

# Repositories to process
REPOS=(
    "atrium-alto-postprocess"
    "atrium-page-classification"
    "atrium-nlp-enrich"
    "atrium-translator"
    "atrium-project"
    "atrium-llm-enrich"
)

# Repository-specific virtual environments (relative to BASE_DIR/<repo>)
declare -A VENV_PATHS=(
    ["atrium-alto-postprocess"]="venv-alto"
    ["atrium-page-classification"]="venv"
    ["atrium-nlp-enrich"]="venv-nlp"
    ["atrium-translator"]="venv-trans"
    ["atrium-project"]="venv-atrium"
    ["atrium-llm-enrich"]="venv-llm"
)

# ------------------------------------------------------------
# Colors & Formatting
# ------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_separator() { echo -e "${BLUE}==================================================${NC}"; }
print_header() {
    echo
    print_separator
    echo -e "${BLUE}$1${NC}"
    print_separator
}

# ------------------------------------------------------------
# Counters & Status Tracking
# ------------------------------------------------------------

TOTAL_REPOS=${#REPOS[@]}
REPO_INDEX=0

ISSUE_REFRESH_SUCCESS=0
ISSUE_REFRESH_FAILED=0
PRE_COMMIT_SUCCESS=0
PRE_COMMIT_FAILED=0
OVERALL_FAILED=0

declare -a ISSUE_REFRESH_FAILED_REPOS=()
declare -a PRE_COMMIT_FAILED_REPOS=()

fail_repo() { OVERALL_FAILED=1; }

# ------------------------------------------------------------
# Pre-flight checks
# ------------------------------------------------------------

print_header "ATRIUM ecosystem maintenance"
echo "Base directory: $BASE_DIR"
echo "Repositories:   $TOTAL_REPOS"
echo

if [[ ! -d "$BASE_DIR" ]]; then
    echo -e "${RED}ERROR: Base directory does not exist: ${BASE_DIR}${NC}"
    exit 1
fi

export GITHUB_ACCESS_TOKEN=github_pat_11APWHO...oG6

if [[ -z "${GITHUB_ACCESS_TOKEN:-}" ]]; then
    echo -e "${RED}ERROR: GITHUB_ACCESS_TOKEN is not set.${NC}"
    echo "Export it before running this script, for example:"
    echo "  export GITHUB_ACCESS_TOKEN='...'"
    exit 1
fi

# Consolidate dependency checks
for cmd in git gh2md pre-commit; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}ERROR: '$cmd' is not installed or not available in PATH.${NC}"
        exit 1
    fi
done

echo -e "${GREEN}Pre-flight checks passed.${NC}"

# ------------------------------------------------------------
# Main repository loop
# ------------------------------------------------------------

for REPO in "${REPOS[@]}"; do
    ((++REPO_INDEX))

    REPO_DIR="$BASE_DIR/$REPO"
    LOG_DIR="$REPO_DIR/agent_dev_logs"
    ISSUES_DIR="$LOG_DIR/issues"
    VENV_NAME="${VENV_PATHS[$REPO]:-}"
    VENV_DIR="$REPO_DIR/$VENV_NAME"

    print_header "Processing: $GITHUB_ORG/$REPO [Repo $REPO_INDEX of $TOTAL_REPOS]"

    # --- Validate repository ---
    if [[ ! -d "$REPO_DIR" ]] || [[ ! -d "$REPO_DIR/.git" ]]; then
        echo -e "${RED}ERROR: Invalid or missing Git repository at: $REPO_DIR${NC}"
        echo "Skipping $REPO..."

        ((++ISSUE_REFRESH_FAILED))
        ((++PRE_COMMIT_FAILED))
        ISSUE_REFRESH_FAILED_REPOS+=("$REPO")
        PRE_COMMIT_FAILED_REPOS+=("$REPO")
        fail_repo
        continue
    fi

    # --------------------------------------------------------
    # Step 1: Refresh GitHub issues
    # --------------------------------------------------------
    echo -e "\n${YELLOW}Step 1: Refreshing open GitHub issues...${NC}\n"

    mkdir -p "$LOG_DIR"
    pushd "$LOG_DIR" > /dev/null || {
        echo -e "${RED}ERROR: Could not enter $LOG_DIR${NC}"
        ((++ISSUE_REFRESH_FAILED))
        ISSUE_REFRESH_FAILED_REPOS+=("$REPO")
        fail_repo
        continue
    }

    echo "Cleaning up old issues directory..."
    rm -rf "$ISSUES_DIR"
    mkdir -p "$ISSUES_DIR"

    if gh2md "$GITHUB_ORG/$REPO" --no-closed-issues --no-prs --multiple-files "$ISSUES_DIR"; then
        ((++ISSUE_REFRESH_SUCCESS))
        echo -e "\n${GREEN}✓ Issue refresh completed successfully.${NC}"
    else
        ((++ISSUE_REFRESH_FAILED))
        ISSUE_REFRESH_FAILED_REPOS+=("$REPO")
        fail_repo
        echo -e "\n${RED}✗ ERROR: Issue refresh failed for $REPO.${NC}"
    fi

    popd > /dev/null

    # --------------------------------------------------------
    # Step 2: Run pre-commit
    # --------------------------------------------------------
    echo -e "\n${YELLOW}Step 2: Running pre-commit checks...${NC}\n"

    pushd "$REPO_DIR" > /dev/null || {
        echo -e "${RED}ERROR: Could not enter repository: $REPO_DIR${NC}"
        ((++PRE_COMMIT_FAILED))
        PRE_COMMIT_FAILED_REPOS+=("$REPO")
        fail_repo
        continue
    }

    VENV_ACTIVATED=0
    if [[ -n "$VENV_NAME" && -f "$VENV_DIR/bin/activate" ]]; then
        echo "Activating virtual environment: $VENV_DIR"
        # shellcheck disable=SC1091
        source "$VENV_DIR/bin/activate"
        VENV_ACTIVATED=1
    else
        echo -e "${YELLOW}WARNING: Repository-specific virtual environment not found. Using current environment.${NC}"
    fi

    echo -e "\nRunning: pre-commit run --all-files\n"

    # First pass
    if pre-commit run --all-files; then
        ((++PRE_COMMIT_SUCCESS))
        echo -e "\n${GREEN}✓ Pre-commit checks passed cleanly on first pass.${NC}"
    else
        # Second pass after automatic fixes
        echo -e "\n${YELLOW}Pre-commit modified files. Rerunning to verify final state...${NC}\n"

        if pre-commit run --all-files; then
            ((++PRE_COMMIT_SUCCESS))
            echo -e "\n${GREEN}✓ Pre-commit checks passed after automatic fixes.${NC}"
        else
            ((++PRE_COMMIT_FAILED))
            PRE_COMMIT_FAILED_REPOS+=("$REPO")
            fail_repo
            echo -e "\n${RED}✗ ERROR: Pre-commit checks still failing for $REPO.${NC}"
        fi
    fi

    # Clean up environment
    if [[ "$VENV_ACTIVATED" -eq 1 ]]; then
        deactivate
    fi

    popd > /dev/null
    echo -e "\nFinished processing $REPO."

done

# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

print_header "ATRIUM ecosystem maintenance summary"

echo "Repositories processed:        $TOTAL_REPOS"
echo
echo "Issue refresh:"
echo -e "  ${GREEN}Successful:${NC}                  $ISSUE_REFRESH_SUCCESS"
echo -e "  ${RED}Failed:${NC}                      $ISSUE_REFRESH_FAILED"
echo
echo "Pre-commit:"
echo -e "  ${GREEN}Successful:${NC}                  $PRE_COMMIT_SUCCESS"
echo -e "  ${RED}Failed:${NC}                      $PRE_COMMIT_FAILED"
echo

if [[ "${#ISSUE_REFRESH_FAILED_REPOS[@]}" -gt 0 ]]; then
    echo -e "\n${RED}Repositories with failed issue refresh:${NC}"
    for REPO in "${ISSUE_REFRESH_FAILED_REPOS[@]}"; do echo "  - $REPO"; done
fi

if [[ "${#PRE_COMMIT_FAILED_REPOS[@]}" -gt 0 ]]; then
    echo -e "\n${RED}Repositories with failed pre-commit:${NC}"
    for REPO in "${PRE_COMMIT_FAILED_REPOS[@]}"; do echo "  - $REPO"; done
fi

echo

if [[ "$OVERALL_FAILED" -eq 0 ]]; then
    echo -e "${GREEN}🎉 All repositories were successfully refreshed and passed pre-commit.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Maintenance completed with failures. Review the errors above.${NC}"
    exit 1
fi
