#!/usr/bin/env bash
# Governance contract compliance checker
# Validates the contract is complete enough to operate.
# Exit code 0 = ready, non-zero = contract needs work.

set -euo pipefail

CONTRACT="$(dirname "$0")/../governance/CONTRACT.md"
LOOP_DIR="$(dirname "$0")/../governance/loop"
FAILURES=0
WARNINGS=0

fail() {
  echo "FAIL: $1"
  FAILURES=$((FAILURES + 1))
}

warn() {
  echo "WARN: $1"
  WARNINGS=$((WARNINGS + 1))
}

pass() {
  echo "PASS: $1"
}

# --- Contract exists ---
if [[ ! -f "$CONTRACT" ]]; then
  echo "FATAL: governance/CONTRACT.md not found"
  exit 2
fi

# --- Required sections ---
for section in "Identity" "Intent" "The Loop" "Scope" "Boundaries" "Success Signals" "Decision Rights" "Amendment Process"; do
  if grep -q "## [0-9]*\. $section" "$CONTRACT"; then
    pass "Section '$section' present"
  else
    fail "Missing required section: $section"
  fi
done

# --- Intent is filled (the most important section) ---
VISION=$(awk '/^\*\*Vision:\*\*/{print}' "$CONTRACT")
HYPOTHESIS=$(awk '/^\*\*Current hypothesis:\*\*/{print}' "$CONTRACT")
if echo "$VISION" | grep -q '___'; then
  fail "Vision is blank — steward must state intent before agent can build"
else
  pass "Vision is stated"
fi
if echo "$HYPOTHESIS" | grep -q '___'; then
  warn "No current hypothesis — agent will need to help form one"
else
  pass "Hypothesis is stated"
fi

# --- At least one success signal exists ---
LEADING=$(awk '/### Leading indicators/,/### Lagging/' "$CONTRACT" | grep -c '___' 2>/dev/null || true)
LAGGING=$(awk '/### Lagging indicators/,/### Current blind/' "$CONTRACT" | grep -c '___' 2>/dev/null || true)
TOTAL_BLANKS=$(grep -c '___' "$CONTRACT" 2>/dev/null || true)

if [[ "$TOTAL_BLANKS" -gt 0 ]]; then
  warn "Contract has $TOTAL_BLANKS unfilled fields — the loop will refine these"
fi

# --- Scope is defined ---
IN_SCOPE=$(awk '/In scope:/{print}' "$CONTRACT")
if echo "$IN_SCOPE" | grep -q '___'; then
  fail "Scope not defined — agent doesn't know what it's allowed to build"
else
  pass "Scope is defined"
fi

# --- Loop directory exists ---
if [[ -d "$LOOP_DIR" ]]; then
  ENTRIES=$(find "$LOOP_DIR" -name '*.md' 2>/dev/null | wc -l)
  pass "Loop directory exists ($ENTRIES entries)"
else
  warn "No governance/loop/ directory — will be created on first loop entry"
fi

# --- Contract version ---
if grep -qP 'Contract version.*\| `[0-9]+\.[0-9]+\.[0-9]+`' "$CONTRACT"; then
  pass "Contract version set"
else
  fail "Contract version not set"
fi

# --- Summary ---
echo ""
echo "================================"
if [[ "$FAILURES" -eq 0 && "$WARNINGS" -eq 0 ]]; then
  echo "CONTRACT READY — agent can operate"
  exit 0
elif [[ "$FAILURES" -eq 0 ]]; then
  echo "CONTRACT OPERABLE with $WARNINGS warning(s) — loop will refine"
  exit 0
else
  echo "$FAILURES BLOCKER(S), $WARNINGS WARNING(S)"
  echo "Agent should help steward resolve blockers before building"
  exit 1
fi
