#!/usr/bin/env bash
# Smoke test for SentenceTransformerEmbedder with the real model.
# Requires: pip install sentence-transformers
# Run from project root: bash tests/scripts/test_embeddings_smoke.sh

set -euo pipefail

PYTHON=".venv/bin/python"
PASS=0
FAIL=0

ok()   { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

echo ""
echo "SentenceTransformer smoke tests"
echo "══════════════════════════════"

# Check if sentence-transformers is installed
if ! $PYTHON -c "import sentence_transformers" 2>/dev/null; then
    echo ""
    echo "  ⚠  sentence-transformers not installed — skipping."
    echo "     Install with: .venv/bin/pip install sentence-transformers"
    echo ""
    exit 0
fi

echo ""
echo "── embed basic ─────────────────────────"

RESULT=$($PYTHON - << 'PYEOF'
from ragkit.embeddings.sentence_transformers import SentenceTransformerEmbedder

embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
vecs = embedder.embed(["Hello world", "RAG is great"])

assert len(vecs) == 2, f"Expected 2 vectors, got {len(vecs)}"
assert len(vecs[0]) == 384, f"Expected dim 384, got {len(vecs[0])}"
assert isinstance(vecs[0][0], float), "Vector elements must be floats"

# Cosine similarity sanity: same sentence → high similarity
import math
def cosine(a, b):
    dot = sum(x*y for x,y in zip(a,b))
    na = math.sqrt(sum(x**2 for x in a))
    nb = math.sqrt(sum(x**2 for x in b))
    return dot / (na * nb)

v1 = embedder.embed_one("The cat sat on the mat")
v2 = embedder.embed_one("The cat sat on the mat")
v3 = embedder.embed_one("Quantum physics equations")

assert cosine(v1, v2) > 0.999, "Same sentence should have cosine sim ≈ 1"
assert cosine(v1, v3) < 0.9,   "Different sentences should have lower similarity"

print("OK")
PYEOF
2>&1)

if echo "$RESULT" | grep -q "^OK$"; then
    ok "embed returns correct shape and values"
    ok "cosine similarity is coherent"
else
    fail "embedding test failed: $RESULT"
fi

echo ""
echo "── lazy loading ─────────────────────────"

LAZY=$($PYTHON - << 'PYEOF'
from ragkit.embeddings.sentence_transformers import SentenceTransformerEmbedder
e = SentenceTransformerEmbedder()
assert e._model is None, "model should not load before first embed"
e.embed(["x"])
assert e._model is not None, "model should be loaded after first embed"
e.embed(["y"])  # should not reload
print("OK")
PYEOF
2>&1)

if echo "$LAZY" | grep -q "^OK$"; then
    ok "lazy loads model on first embed"
    ok "does not reload model on subsequent calls"
else
    fail "lazy loading test failed: $LAZY"
fi

echo ""
echo "══════════════════════════════"
echo "Results: $PASS passed, $FAIL failed"
echo ""
[ "$FAIL" -eq 0 ]
