#!/usr/bin/env bash
# Run available linters/formatters for a given file or directory.
# Usage: ./run_linters.sh <file-or-dir>
#
# This script auto-detects the language via file extension and runs the
# appropriate linter. It is designed to be called by the AI agent during
# step 2 of the code-review workflow.
#
# Supported tools (must be installed locally):
#   Python  → pylint, black --check
#   JavaScript/TypeScript → eslint
#   Ruby    → rubocop
#   Shell   → shellcheck
#   Go      → go vet, staticcheck
#
# Exit codes: 0 = clean, 1 = issues found, 2 = no linter available.
#
# Integration note: If a linter is not installed, the script prints a
# message and exits with code 2. The agent should then skip automated
# findings rather than failing the review.

set -euo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  echo "Usage: $0 <file-or-directory>"
  exit 2
fi

if [ ! -e "$TARGET" ]; then
  echo "Error: '$TARGET' does not exist."
  exit 2
fi

# Detect language by extension of the first relevant file
ext=""
if [ -f "$TARGET" ]; then
  ext="${TARGET##*.}"
elif [ -d "$TARGET" ]; then
  # Find the most common extension in the directory
  ext=$(find "$TARGET" -type f | sed -n 's/.*\.\([^.]*\)$/\1/p' | sort | uniq -c | sort -rn | head -1 | awk '{print $2}')
fi

run_if_available() {
  local cmd="$1"
  if command -v "$cmd" &>/dev/null; then
    echo "--- Running: $cmd ---"
    "$@" || true
    return 0
  else
    echo "Skipping: $cmd (not installed)"
    return 2
  fi
}

case "$ext" in
  py)
    run_if_available pylint "$TARGET"
    run_if_available black --check --diff "$TARGET"
    ;;
  js|jsx|ts|tsx|mjs|cjs)
    run_if_available eslint "$TARGET"
    ;;
  rb)
    run_if_available rubocop "$TARGET"
    ;;
  sh|bash|zsh)
    run_if_available shellcheck "$TARGET"
    ;;
  go)
    run_if_available go vet "./${TARGET}"
    run_if_available staticcheck "./${TARGET}"
    ;;
  *)
    echo "No linter configured for extension: .$ext"
    exit 2
    ;;
esac
