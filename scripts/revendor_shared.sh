#!/usr/bin/env bash
#
# revendor_shared.sh — push docs/templates/shared/* into the five tool repos.
#
# WHY THIS EXISTS. The hub does not publish the canonical modules as a package;
# it enforces them by COPY. para-drift.reusable.yml `diff -u`s every file in
# docs/templates/shared/ against its vendored twin in all five tool repos, so a
# hub-side edit is not "landed" until the same bytes exist in five other
# repositories. Until now that copy step was done by hand, and two documents
# (docs/document_schema.md, atrium_document.py's load_schema() error message)
# already told maintainers to "use scripts/revendor_shared.sh" — a script that
# did not exist (issue #10, finding D9).
#
# It is also what makes issue #10 finding G4's atomic window practical: template
# edit + five re-vendorings + retag has to happen inside one window, because a
# moving `v1` makes identical commits fail para-drift in one repo and pass in
# another minutes later. Doing five copies by hand is how that window gets wide.
#
# DESTINATIONS ARE NOT UNIFORM — this is the whole reason a script beats a
# `cp -t`: the tests go to tests/, the service base class goes to service/, and
# everything else sits at the repo root next to the code that imports it. Adding
# a file to docs/templates/shared/ therefore means adding a row to SHARED_FILES
# below AND a parity step to para-drift.reusable.yml, or the new file travels
# nowhere and is enforced nowhere.
#
# Usage:
#   scripts/revendor_shared.sh                      # re-vendor into ../atrium-*
#   scripts/revendor_shared.sh --root ~/src         # siblings live elsewhere
#   scripts/revendor_shared.sh --check              # verify only, write nothing
#   scripts/revendor_shared.sh --repo atrium-translator [--repo ...]
#
# Exit code is 0 when every destination matches the canonical byte-for-byte —
# i.e. when para-drift would pass — and 1 otherwise. Re-running on an
# already-vendored tree is a no-op that reports "up to date", so it is safe in a
# loop, in a pre-push hook, or twice by accident.

set -euo pipefail

HUB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHARED_DIR="$HUB_ROOT/docs/templates/shared"

# Default sibling root: the directory the hub checkout itself sits in, which is
# the layout every ATRIUM working copy uses (…/alto/atrium-project,
# …/alto/atrium-translator, …). Overridable because CI and one-off clones do not
# have to honour it.
SIBLING_ROOT="${ATRIUM_SIBLING_ROOT:-$(dirname "$HUB_ROOT")}"

ALL_REPOS=(
    atrium-page-classification
    atrium-alto-postprocess
    atrium-nlp-enrich
    atrium-translator
    atrium-llm-enrich
)

# canonical filename -> path RELATIVE TO THE TOOL REPO ROOT.
# Keep in step with para-drift.reusable.yml's diff steps; the two lists are the
# same contract read from opposite ends (this one writes it, that one enforces
# it).
declare -A SHARED_FILES=(
    ["atrium_paradata.py"]="atrium_paradata.py"
    ["para_licenses.py"]="para_licenses.py"
    ["test_para_licenses.py"]="tests/test_para_licenses.py"
    ["test_document_originators.py"]="tests/test_document_originators.py"
    ["atrium_service.py"]="service/atrium_service.py"
    ["check_version.py"]="check_version.py"
    ["atrium_document.py"]="atrium_document.py"
    ["atrium_document.schema.json"]="atrium_document.schema.json"
)

CHECK_ONLY=0
REPOS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --root)
            [[ $# -ge 2 ]] || { echo "ERROR: --root needs a directory" >&2; exit 2; }
            SIBLING_ROOT="$2"
            shift 2
            ;;
        --repo)
            [[ $# -ge 2 ]] || { echo "ERROR: --repo needs a repository name" >&2; exit 2; }
            REPOS+=("$2")
            shift 2
            ;;
        --check)
            CHECK_ONLY=1
            shift
            ;;
        -h|--help)
            sed -n '3,40p' "${BASH_SOURCE[0]}"
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument '$1' (try --help)" >&2
            exit 2
            ;;
    esac
done

[[ ${#REPOS[@]} -gt 0 ]] || REPOS=("${ALL_REPOS[@]}")

[[ -d "$SHARED_DIR" ]] || {
    echo "ERROR: canonical directory not found: $SHARED_DIR" >&2
    exit 1
}

echo "Canonical:    $SHARED_DIR"
echo "Sibling root: $SIBLING_ROOT"
echo "Repos:        ${REPOS[*]}"
if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "Mode:         --check (no writes)"
fi
echo

COPIED=0
UNCHANGED=0
DRIFTED=0
FAILED=0

for repo in "${REPOS[@]}"; do
    repo_dir="$SIBLING_ROOT/$repo"
    if [[ ! -d "$repo_dir" ]]; then
        # Not fatal: a maintainer often has only a subset checked out, and
        # failing the whole run would push them back to copying by hand.
        echo "SKIP  $repo — no checkout at $repo_dir"
        FAILED=1
        continue
    fi
    echo "== $repo"

    for name in $(printf '%s\n' "${!SHARED_FILES[@]}" | sort); do
        src="$SHARED_DIR/$name"
        dest="$repo_dir/${SHARED_FILES[$name]}"

        if [[ ! -f "$src" ]]; then
            echo "  FAIL  $name — missing from the canonical directory"
            FAILED=1
            continue
        fi

        if cmp -s "$src" "$dest"; then
            echo "  ok    ${SHARED_FILES[$name]}"
            UNCHANGED=$((UNCHANGED + 1))
            continue
        fi

        if [[ "$CHECK_ONLY" -eq 1 ]]; then
            echo "  DRIFT ${SHARED_FILES[$name]} — differs from the canonical:"
            # Same `diff -u` orientation as the para-drift step, so the output a
            # maintainer reads here is the output they will read in that job's log.
            diff -u "$dest" "$src" || true
            DRIFTED=$((DRIFTED + 1))
            continue
        fi

        # The destination directory always exists in a real tool repo (tests/,
        # service/); creating it rather than failing keeps the script usable on a
        # fresh repo that is adopting the shared set for the first time.
        mkdir -p "$(dirname "$dest")"
        cp -p "$src" "$dest"
        echo "  COPY  ${SHARED_FILES[$name]}"
        COPIED=$((COPIED + 1))
    done
done

# Verify AFTER writing rather than trusting cp: this is the same `diff -u` the
# para-drift step runs, so a clean run here means that check passes. A silent
# half-copy (full disk, read-only checkout, dangling symlink) is exactly the
# failure that would otherwise surface as five red CI runs. Skipped under
# --check, where the loop above already diffed every pair and wrote nothing.
if [[ "$CHECK_ONLY" -eq 0 ]]; then
    echo
    echo "Verifying parity (the diff para-drift.reusable.yml runs):"
    for repo in "${REPOS[@]}"; do
        repo_dir="$SIBLING_ROOT/$repo"
        [[ -d "$repo_dir" ]] || continue
        for name in $(printf '%s\n' "${!SHARED_FILES[@]}" | sort); do
            dest="$repo_dir/${SHARED_FILES[$name]}"
            if ! diff -u "$dest" "$SHARED_DIR/$name" >/dev/null 2>&1; then
                echo "  MISMATCH $repo/${SHARED_FILES[$name]}"
                diff -u "$dest" "$SHARED_DIR/$name" || true
                FAILED=1
            fi
        done
    done
fi

echo
if [[ "$CHECK_ONLY" -eq 1 ]]; then
    echo "Summary: $UNCHANGED in parity, $DRIFTED drifted (nothing written)."
else
    echo "Summary: $COPIED copied, $UNCHANGED already up to date."
fi

if [[ "$FAILED" -ne 0 || "$DRIFTED" -ne 0 ]]; then
    echo "RESULT: NOT in parity — para-drift would fail. See the lines above." >&2
    exit 1
fi

echo "RESULT: all ${#SHARED_FILES[@]} canonical files are in parity across ${#REPOS[@]} repo(s)."
echo
echo "Next, per issue #10 finding G4: commit the tool-repo copies and the hub"
echo "edit in ONE window, then move \`v1\` — never before the copies have landed."
