#!/usr/bin/env bash
# verify.sh — critic-panel fan-out gate for the critic-panel example.
# Derived from the critic-panel recipe in templates/verifier-library.yaml.
# EXIT 0 (GREEN) iff >= QUORUM_K critics score ARTIFACT >= THRESHOLD.
# Emits critics.jsonl (one JSON line per critic) in the working directory.
# READ-ONLY: rubric.md and artifact.md are never modified.
set -euo pipefail

RUBRIC="rubric.md"
ARTIFACT="artifact.md"
N=3
QUORUM_K=2
THRESHOLD=80

sha() {
  local f="$1"
  (sha256sum "$f" 2>/dev/null || shasum -a 256 "$f") | awk '{print $1}'
}

rsha=$(sha "$RUBRIC")
asha=$(sha "$ARTIFACT")
pass=0

while IFS= read -r i; do
  script="./critic-${i}.sh"
  score=$(bash "$script" --rubric "$RUBRIC" --artifact "$ARTIFACT") || score=0
  ok=false
  if [ "${score:-0}" -ge "$THRESHOLD" ]; then
    ok=true
    pass=$((pass + 1))
  fi
  provider=$(grep -m1 -oE 'PROVIDER=[A-Za-z0-9_-]+' "$script" | cut -d= -f2 || true)
  printf '{"ts":"%s","critic":"critic-%s","provider":"%s","score":%s,"threshold":%s,"pass":%s,"rubric_sha":"%s","artifact_sha":"%s","n":%s,"quorum_k":%s}\n' \
    "$(date -u +%FT%TZ)" "$i" "${provider:-unknown}" "${score:-0}" \
    "$THRESHOLD" "$ok" "$rsha" "$asha" "$N" "$QUORUM_K" >> critics.jsonl
done < <(seq 1 "$N")

if [ "$pass" -ge "$QUORUM_K" ]; then
  echo "critic-panel: quorum PASS ($pass/$N, need $QUORUM_K)"
  exit 0
else
  echo "critic-panel: quorum FAIL ($pass/$N, need $QUORUM_K)" >&2
  exit 1
fi
