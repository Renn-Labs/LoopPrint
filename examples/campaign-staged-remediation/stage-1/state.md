# Loop state — campaign-remedi-stage-1

> Durable record. Append each iteration; never reset until the gate is GREEN.

- **Goal:** Derive and commit a machine-checkable spec for the target module.
- **Pattern:** spec-driven (gate)
- **Verifier:** `bash verify.sh` — GREEN means spec.md exists
- **Stop:** max_iters 10 · halt: touch `HALT`
- **Status:** OPEN
- **Campaign:** campaign-staged-remediation / stage 1 of 2

## Iteration log

| # | timestamp | action | spec.md | verifier |
|-|-|-|-|-|
| 0 | — | seed — spec.md absent | absent | RED |

## Hand-off

On GREEN: commit spec.md, notify the campaign operator for the inter-stage human checkpoint.
The operator reviews spec.md before authorising stage 2.
