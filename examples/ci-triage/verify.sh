#!/usr/bin/env bash
# verify.sh — external gate for the ci-triage loop.
# GREEN (exit 0) only when the whole suite passes: the target test fixed AND no regressions.
set -euo pipefail

# Run the full suite. Adapt to your stack (pytest -q, go test ./..., cargo test, etc.).
npm test --silent

# npm test exits non-zero on any failure, so reaching here means GREEN.
echo "verify: suite GREEN"
