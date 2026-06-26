# Decision Gate (Tier 0) — "Is this even a loop?"

The first and most valuable step. A loop is infrastructure; building one for the wrong task wastes more than it
saves. Run this before designing anything.

## The 4 conditions (ALL must hold)

A loop pays off only when every one of these is true:

1. **It recurs.** The task happens repeatedly, so the cost of building the loop amortizes across many runs.
   *One-off? → single high-quality pass, not a loop.*

2. **An objective gate can reject bad output.** You can name a test / build / lint / reproduction / rubric / or a
   distinct reviewer that says yes-or-no without the maker's opinion.
   *Can't write the gate? → you can't close the loop; don't open it.*

3. **The budget absorbs retries.** Iterating to a good answer is cheaper (time/tokens/money) than producing it
   right the first time by hand.
   *Each retry is expensive or risky? → do it carefully once.*

4. **The agent can run what it writes.** There's a real execution feedback signal each cycle — not a human in the
   middle of every iteration.
   *Needs a human judgment every step? → that's a workflow, not an autonomous loop.*

## 30-second checklist

Answer fast. Any "no" in 1–4 is a hard stop; the rest shape the design.

- [ ] **Recurs?** (cond. 1)
- [ ] **Objective gate exists / writable?** (cond. 2)
- [ ] **Retries affordable?** (cond. 3)
- [ ] **Agent can execute + observe results?** (cond. 4)
- [ ] **Failure is reversible** (or the irreversible steps can be gated behind a human)?
- [ ] **Clear "done"** — a machine or named reviewer can confirm success?
- [ ] **Safety limit** you're willing to set (max iters / budget / deadline)?

## Verdict

- **Pass (1–4 all yes):** proceed to design. Note any unchecked safety items as required artifacts.
- **Fail (any of 1–4 no):** recommend the honest alternative and stop:
  - Not recurring / retries costly → **one high-quality pass**.
  - No objective gate → **human-reviewed task**, not an autonomous loop.
  - Irreversible + judgment-heavy (prod deploy, auth, payments, "is this good enough") → **human-gated process**.

## The metric

Optimize **cost-per-accepted-change**, not tokens spent or iterations run. A loop that burns 10× the tokens but
lands accepted changes hands-off can still win; one that loops cheaply forever without passing the gate loses.

## Good vs bad loops (quick reference)

| Good (build the loop) | Bad (don't) |
|-|-|
| CI failure triage | Architecture rewrites |
| Dependency bumps | Auth / payments changes |
| Lint / format auto-fix | Production deploys |
| Flaky-test reproduction | Judgment-call "is this good?" |
| Issue → PR on well-tested code | Anything irreversible without a human gate |
