#!/usr/bin/env bash
#
# NexusRAG Smoke Test Suite
# Validates deployment health by probing key endpoints.
#
# Usage: ./smoke-test.sh [BASE_URL]
#   BASE_URL defaults to http://localhost:5000
#

set -euo pipefail

BASE_URL="${1:-http://localhost:5000}"
DATA_API_URL="${DATA_API_URL:-http://localhost:3456}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
TOTAL=0
TIMEOUT=10

log_info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_pass()  { echo -e "${GREEN}[PASS]${NC}  $*"; ((PASS++)); ((TOTAL++)); }
log_fail()  { echo -e "${RED}[FAIL]${NC}  $*"; ((FAIL++)); ((TOTAL++)); }
log_skip()  { echo -e "${YELLOW}[SKIP]${NC}  $*"; ((TOTAL++)); }

check_endpoint() {
  local name="$1"
  local url="$2"
  local expected_status="${3:-200}"

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "${TIMEOUT}" "${url}" 2>/dev/null || echo "000")

  if [[ "${http_code}" == "${expected_status}" ]]; then
    log_pass "${name} - ${url} (HTTP ${http_code})"
  elif [[ "${http_code}" == "000" ]]; then
    log_fail "${name} - ${url} (connection refused or timeout)"
  else
    log_fail "${name} - ${url} (expected HTTP ${expected_status}, got ${http_code})"
  fi
}

check_json_endpoint() {
  local name="$1"
  local url="$2"
  local jq_filter="${3:-.}"

  local response
  response=$(curl -s --max-time "${TIMEOUT}" "${url}" 2>/dev/null || echo "")

  if [[ -z "${response}" ]]; then
    log_fail "${name} - ${url} (no response)"
    return
  fi

  if echo "${response}" | jq -e "${jq_filter}" &>/dev/null; then
    log_pass "${name} - ${url} (valid JSON)"
  else
    log_fail "${name} - ${url} (invalid JSON or filter failed)"
  fi
}

test_inquire() {
  local name="Gateway /api/inquire"
  local url="${BASE_URL}/api/inquire"

  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 \
    -X POST "${url}" \
    -H "Content-Type: application/json" \
    -d '{"question": "What is retrieval-augmented generation?"}' 2>/dev/null || echo "000")

  if [[ "${http_code}" =~ ^(200|201|202)$ ]]; then
    log_pass "${name} - POST ${url} (HTTP ${http_code})"
  elif [[ "${http_code}" == "000" ]]; then
    log_fail "${name} - POST ${url} (connection refused or timeout)"
  elif [[ "${http_code}" == "401" || "${http_code}" == "403" ]]; then
    log_skip "${name} - POST ${url} (auth required, HTTP ${http_code})"
  else
    log_fail "${name} - POST ${url} (expected HTTP 200, got ${http_code})"
  fi
}

# ──────────────────────────────────────────────
# Test Execution
# ──────────────────────────────────────────────

echo ""
echo "========================================"
echo "  NexusRAG Smoke Test Suite"
echo "  Gateway:  ${BASE_URL}"
echo "  Data API: ${DATA_API_URL}"
echo "========================================"
echo ""

log_info "Testing Gateway health endpoints..."
check_endpoint "Gateway /alive"  "${BASE_URL}/alive"
check_endpoint "Gateway /ready"  "${BASE_URL}/ready"
check_endpoint "Gateway /health" "${BASE_URL}/health"

echo ""
log_info "Testing Data API endpoints..."
check_endpoint "Data API /ping" "${DATA_API_URL}/ping"

echo ""
log_info "Testing Gateway API endpoints..."
check_json_endpoint "Platform Info"    "${BASE_URL}/api/platform/info"   ".version"
check_json_endpoint "Platform Tools"   "${BASE_URL}/api/platform/tools"  "."
check_json_endpoint "Search Modes"     "${BASE_URL}/api/search-modes"    "."
check_json_endpoint "Conversations"    "${BASE_URL}/api/conversations"   "."

echo ""
log_info "Testing inquiry endpoint..."
test_inquire

# ──────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────

echo ""
echo "========================================"
echo "  Results: ${PASS} passed, ${FAIL} failed (${TOTAL} total)"
echo "========================================"
echo ""

if [[ "${FAIL}" -gt 0 ]]; then
  log_fail "Smoke tests completed with ${FAIL} failure(s)."
  exit 1
else
  log_pass "All smoke tests passed."
  exit 0
fi
