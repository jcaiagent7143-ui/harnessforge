#!/usr/bin/env bash
# Apache Airflow × workflow-agent blueprint.
set -euo pipefail

REPO="https://github.com/apache/airflow.git"
# Pinned for reproducibility — bump alongside the hero-demo screenshots.
SHA="${HERO_AIRFLOW_SHA:-477b1482e7e242f3717aa7ffc490af4592ada3d3}"
WORK="${HERO_WORK:-/tmp/harness-hero-airflow-workflow}"

echo "[hero] cloning $REPO @ $SHA → $WORK (shallow)"
rm -rf "$WORK"
git clone --quiet --depth=1 "$REPO" "$WORK"
if [ "$SHA" != "main" ]; then
  (cd "$WORK" && git fetch --quiet --depth=1 origin "$SHA" && git checkout --quiet "$SHA")
fi

echo "[hero] running: harness init --no-llm --blueprint workflow-agent"
harness init "$WORK" --no-llm --blueprint workflow-agent --force

echo "[hero] generated harness files:"
(cd "$WORK" && find . -maxdepth 3 \
  \( -name 'AGENTS.md' -o -name 'SOUL.md' -o -name 'TOOLS.md' -o -name 'MEMORY.md' \
     -o -name 'harness.config.json' -o -path './.harness/*' -o -path './SKILLS/*' \) | sort)

echo "[hero] running: harness verify --json"
harness verify "$WORK" --json

echo "[hero] ✓ done"
