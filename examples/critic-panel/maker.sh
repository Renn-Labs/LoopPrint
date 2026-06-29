#!/usr/bin/env bash
# maker.sh — demo maker for the critic-panel example.
# Real use: swap the stub block for a live dispatch, e.g.:
#   claude -p "Improve artifact.md to score >= 80 on rubric.md. Output the full revised file."
# PROVIDER=claude
set -euo pipefail

RUBRIC="${1:-rubric.md}"
ARTIFACT="${2:-artifact.md}"

[ -f "$RUBRIC" ]   || { echo "maker: rubric not found: $RUBRIC" >&2; exit 1; }
[ -f "$ARTIFACT" ] || { echo "maker: artifact not found: $ARTIFACT" >&2; exit 1; }

# Deterministic stub: append a revision marker so each iteration produces a
# distinct artifact (no live LLM required for the demo).
printf '\n<!-- iteration: %s -->\n' "$(date -u +%FT%TZ)" >> "$ARTIFACT"
echo "maker: artifact.md updated (stub — swap for live LLM dispatch in real use)"
