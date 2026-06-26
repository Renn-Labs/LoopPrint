# Loop state — ci-triage

> Durable record. Append, never reset until GREEN.

- **Goal:** The failing test(s) on the current branch pass, with no other test regressing.
- **Pattern:** morty
- **Verifier:** `npm test --silent` — GREEN means the failing test passes and nothing else regressed
- **Stop:** verifier GREEN · max_iters 6 · budget 20min · halt: touch `HALT`
- **Status:** OPEN
- **Started:** 2026-06-24T00:00Z

## Iteration log

| # | timestamp | change made | verifier | result / next |
|-|-|-|-|-|
| 0 | 2026-06-24T00:00Z | baseline: `auth.test.ts › refresh token` throws `TypeError: exp undefined` | RED | hypothesis: token decode returns undefined `exp`; check clock-skew guard |

## Open hypotheses
- The refresh path reads `payload.exp` before verifying the token decoded; a malformed token yields `undefined`.

## Decisions & dead ends
- (none yet)

## Hand-off / escalation
- If still RED at iter 6: capture the failing payload, hand to a human — likely a contract change upstream.
