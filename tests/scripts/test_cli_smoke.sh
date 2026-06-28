#!/usr/bin/env bash
# Smoke tests for the ragkit CLI — run from the project root:
#   bash tests/scripts/test_cli_smoke.sh

set -euo pipefail

RAG=".venv/bin/rag"
PASS=0
FAIL=0
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# ── helpers ──────────────────────────────────────────────────────────────────

ok() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

assert_exit_ok() {
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label (expected exit 0)"; fi
}

assert_exit_fail() {
    local label="$1"; shift
    if ! "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label (expected non-zero exit)"; fi
}

assert_output_contains() {
    local label="$1"; local pattern="$2"; shift 2
    local out; out=$("$@" 2>&1) || true
    if echo "$out" | grep -qi "$pattern"; then ok "$label"; else fail "$label (missing: $pattern)"; fi
}

# ── tests ────────────────────────────────────────────────────────────────────

echo ""
echo "RAGKit CLI smoke tests"
echo "══════════════════════"

# --help
echo ""
echo "── rag --help ─────────────────────────"
assert_exit_ok       "exits 0"                      $RAG --help
assert_output_contains "shows commands"  "Commands"  $RAG --help
assert_output_contains "shows init"      "init"      $RAG --help
assert_output_contains "shows serve"     "serve"     $RAG --help
assert_output_contains "shows dev"       "dev"       $RAG --help

# rag init
echo ""
echo "── rag init ────────────────────────────"
PROJ="$TMPDIR/myapp"
mkdir -p "$PROJ"
assert_exit_ok            "exits 0"                     $RAG init --name myapp "$PROJ"
assert_exit_ok            "rag.yaml created"            test -f "$PROJ/rag.yaml"
assert_exit_ok            ".env created"                test -f "$PROJ/.env"
mkdir -p "$TMPDIR/p2"
assert_output_contains    "mentions project name"       "myapp"   $RAG init --name myapp2 "$TMPDIR/p2"
assert_exit_fail          "fails if yaml already exists" $RAG init "$PROJ"

# verify rag.yaml content
if grep -q "myapp" "$PROJ/rag.yaml"; then
    ok "rag.yaml contains project name"
else
    fail "rag.yaml missing project name"
fi

if grep -q "openrouter" "$PROJ/rag.yaml"; then
    ok "rag.yaml contains model config"
else
    fail "rag.yaml missing model config"
fi

# rag serve — fastapi/uvicorn not installed → expect error message
echo ""
echo "── rag serve (no deps) ─────────────────"
SERVE_CFG="$TMPDIR/serve.yaml"
echo "project:" > "$SERVE_CFG"
echo "  name: test" >> "$SERVE_CFG"

SERVE_OUT=$($RAG serve --config "$SERVE_CFG" 2>&1) || true
if echo "$SERVE_OUT" | grep -qi "fastapi\|uvicorn\|pip install"; then
    ok "prints install hint when deps missing"
else
    fail "no install hint found (got: $SERVE_OUT)"
fi

# rag dev — pipe "exit" to stdin via EOFError path
echo ""
echo "── rag dev (piped input) ───────────────"
DEV_CFG="$TMPDIR/dev.yaml"
echo "project:" > "$DEV_CFG"
echo "  name: test" >> "$DEV_CFG"

# Pipe empty input → triggers EOFError → should exit 0
DEV_EXIT=0
echo "" | $RAG dev --config "$DEV_CFG" 2>/dev/null || DEV_EXIT=$?
if [ "$DEV_EXIT" -eq 0 ]; then
    ok "dev exits 0 on EOF"
else
    fail "dev exited $DEV_EXIT on EOF (expected 0)"
fi

# Pipe "exit" keyword → should exit 0
DEV_EXIT=0
printf "exit\n" | $RAG dev --config "$DEV_CFG" 2>/dev/null || DEV_EXIT=$?
if [ "$DEV_EXIT" -eq 0 ]; then
    ok "dev exits 0 on 'exit' command"
else
    fail "dev exited $DEV_EXIT on 'exit' (expected 0)"
fi

# ── summary ──────────────────────────────────────────────────────────────────

echo ""
echo "══════════════════════"
echo "Results: $PASS passed, $FAIL failed"
echo ""
[ "$FAIL" -eq 0 ]
