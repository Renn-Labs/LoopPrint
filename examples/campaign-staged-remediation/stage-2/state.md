# Loop state — campaign-remedi-stage-2

> Durable record. Append each iteration; never reset until the gate is GREEN.

- **Goal:** Remediate all findings from the spec-derived test suite.
- **Pattern:** spec-driven (gate)
- **Verifier:** `bash verify.sh` — GREEN means remediated.flag exists
- **Stop:** max_iters 10 · halt: touch `HALT`
- **Status:** OPEN (awaiting stage-1 human checkpoint)
- **Campaign:** campaign-staged-remediation / stage 2 of 2

## Pre-condition

Stage 2 must not start until:
1. Stage 1 has exited 0 (spec.md committed).
2. A human has reviewed spec.md and approved the transition.

## Iteration log

| # | timestamp | finding addressed | remediated.flag | verifier |
|-|-|-|-|-|
| 0 | — | seed — awaiting stage-1 completion | absent | RED |

## Hand-off

On GREEN: commit the remediated code. Campaign complete. Archive state files.
If max_iters reached without GREEN: open an issue with remaining findings; hand to team.
