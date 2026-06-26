# Loop state — <slug>

> Durable record for this loop. **Append, never reset** until the goal is met. This is the loop's memory:
> what was tried, what failed, what's next. The runner writes here every iteration.

- **Goal:** <one-sentence, testable>
- **Pattern:** <morty | spec-driven | performance | hybrid>
- **Verifier:** `<external command or named reviewer>` — GREEN means: <what a pass proves>
- **Stop:** <success condition> · max_iters <N> · budget <…> · halt: touch `HALT`
- **Status:** OPEN
- **Started:** <YYYY-MM-DDThh:mmZ>

## Iteration log

| # | timestamp | change made | verifier | result / next |
|-|-|-|-|-|
| 0 | <ts> | baseline — measured/observed starting point | <RED/—> | <hypothesis for iter 1> |

## Open hypotheses
- <current best guess at the cause / approach, and why>

## Decisions & dead ends
- <approaches ruled out, so the loop doesn't retry them>

## Hand-off / escalation
- <if stopped without GREEN: what's blocked, what a human needs to decide>
