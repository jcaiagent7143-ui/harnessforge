#!/usr/bin/env bash
# Zulip × support-agent blueprint.
set -euo pipefail

REPO="https://github.com/zulip/zulip.git"
# Pinned for reproducibility — bump alongside the hero-demo screenshots.
SHA="${HERO_ZULIP_SHA:-14b3cfb1331772c5d3e86e9e3eb6db84c7c52cc6}"
WORK="${HERO_WORK:-/tmp/harness-hero-zulip-support}"

echo "[hero] cloning $REPO @ $SHA → $WORK (shallow)"
rm -rf "$WORK"
git clone --quiet --depth=1 "$REPO" "$WORK"
if [ "$SHA" != "main" ]; then
  (cd "$WORK" && git fetch --quiet --depth=1 origin "$SHA" && git checkout --quiet "$SHA")
fi

echo "[hero] running: harness init --no-llm --blueprint support-agent"
harness init "$WORK" --no-llm --blueprint support-agent --force

echo "[hero] generated harness files:"
(cd "$WORK" && find . -maxdepth 3 \
  \( -name 'AGENTS.md' -o -name 'SOUL.md' -o -name 'TOOLS.md' -o -name 'MEMORY.md' \
     -o -name 'harness.config.json' -o -path './.harness/*' -o -path './SKILLS/*' \) | sort)

echo "[hero] running: harness verify --json"
harness verify "$WORK" --json

echo "[hero] ✓ done"
