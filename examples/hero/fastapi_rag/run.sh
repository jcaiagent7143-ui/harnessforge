#!/usr/bin/env bash
# FastAPI full-stack template × rag-agent blueprint.
# Reproducible: clones a pinned SHA, no network for harness itself.
set -euo pipefail

# Pin to a specific commit so output is reproducible.
REPO="https://github.com/fastapi/full-stack-fastapi-template.git"
# Pinned for reproducibility — bump alongside the hero-demo screenshots.
# Override at runtime: HERO_FASTAPI_SHA=<sha> ./run.sh
SHA="${HERO_FASTAPI_SHA:-33fa827e7eb5578d2519186bd30786f838ce5714}"
WORK="${HERO_WORK:-/tmp/harness-hero-fastapi-rag}"

echo "[hero] cloning $REPO @ $SHA → $WORK"
rm -rf "$WORK"
git clone --quiet --depth=1 "$REPO" "$WORK"
if [ "$SHA" != "main" ]; then
  (cd "$WORK" && git fetch --quiet --depth=1 origin "$SHA" && git checkout --quiet "$SHA")
fi

echo "[hero] running: harness init --no-llm --blueprint rag-agent"
harness init "$WORK" --no-llm --blueprint rag-agent --force

echo "[hero] generated tree (depth 2):"
(cd "$WORK" && find . -maxdepth 3 \( -path './.git' -o -path './.venv' -o -path './node_modules' \) -prune -o \
  \( -name 'AGENTS.md' -o -name 'SOUL.md' -o -name 'TOOLS.md' -o -name 'MEMORY.md' \
     -o -name 'harness.config.json' -o -path './.harness/*' -o -path './SKILLS/*' \
     -o -path './.claude/*' -o -path './.cursor/*' -o -path './.continue/*' -o -path './.windsurf/*' \) -print | sort)

echo "[hero] running: harness verify --json"
harness verify "$WORK" --json

echo "[hero] ✓ done"
