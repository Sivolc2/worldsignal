#!/usr/bin/env bash
# Boundary compliance checker
# Verifies the repo state doesn't violate boundaries defined in CONTRACT.md.
# Designed to be run by the agent after each session.

set -euo pipefail

CONTRACT="$(dirname "$0")/../governance/CONTRACT.md"
REPO_ROOT="$(dirname "$0")/.."
FAILURES=0

fail() {
  echo "FAIL: $1"
  FAILURES=$((FAILURES + 1))
}

pass() {
  echo "PASS: $1"
}

# --- Parse max files limit from contract ---
MAX_FILES=$(grep -oP 'Max files created per session.*\| `\K[0-9]+' "$CONTRACT" 2>/dev/null || echo "")
if [[ -n "$MAX_FILES" ]]; then
  # Count non-governance, non-test, non-config files
  CREATED=$(find "$REPO_ROOT" -type f \
    ! -path '*/.git/*' \
    ! -path '*/governance/*' \
    ! -path '*/tests/*' \
    ! -name 'CLAUDE.md' \
    ! -name '.gitignore' \
    ! -name 'README.md' \
    2>/dev/null | wc -l)
  if [[ "$CREATED" -le "$MAX_FILES" ]]; then
    pass "File count ($CREATED) within limit ($MAX_FILES)"
  else
    fail "File count ($CREATED) exceeds limit ($MAX_FILES)"
  fi
else
  echo "SKIP: Max files limit not set in contract"
fi

# --- Parse forbidden actions (placeholder for future expansion) ---
FORBIDDEN=$(awk '/Forbidden actions/{gsub(/.*\| `/, ""); gsub(/`.*/, ""); print}' "$CONTRACT" 2>/dev/null || echo "___")
if [[ "$FORBIDDEN" != "___" && -n "$FORBIDDEN" ]]; then
  pass "Forbidden actions defined: $FORBIDDEN (manual review required)"
else
  echo "SKIP: No forbidden actions defined"
fi

# --- Check no secrets committed ---
SECRETS_PATTERNS=(".env" "credentials.json" "*.pem" "*.key" "secret*")
for pat in "${SECRETS_PATTERNS[@]}"; do
  FOUND=$(find "$REPO_ROOT" -name "$pat" ! -path '*/.git/*' ! -name '*.example' 2>/dev/null | head -5)
  if [[ -n "$FOUND" ]]; then
    fail "Potential secret file found: $FOUND"
  fi
done
pass "No obvious secret files detected"

# --- Summary ---
echo ""
echo "================================"
if [[ "$FAILURES" -eq 0 ]]; then
  echo "ALL BOUNDARY CHECKS PASSED"
  exit 0
else
  echo "$FAILURES BOUNDARY CHECK(S) FAILED"
  exit 1
fi
