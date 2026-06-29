# Pattern library

Four loop shapes. Pick by the task; each maps cleanly onto the four atoms and pins down the *verifier*, which is
the part people get wrong. Compose them when real work spans several (that's Hybrid).

---

## 1. MORTY — debug sub-loop

**For:** a specific, reproducible bug. The canonical debugging loop.

**Shape:**
1. **Reproduce** — capture a failing case as an automated check (this becomes the verifier).
2. **Isolate** — narrow the cause (bisect, trace, binary-search the inputs).
3. **Hypothesize** — name the *cause*, distinguished from the *symptom*.
4. **Minimal fix** — change the smallest thing that addresses the cause.
5. **Verify** — run the reproduction; it must go green. Re-run the broader suite for regressions.
6. **Log state** — record hypothesis tried, result, next step.

**Atoms:** Goal = "bug X no longer reproduces." State = repro + hypothesis log. **Verifier = the reproduction
test passes** (external, objective). Stop = green repro + no regressions, or N hypotheses exhausted → escalate.

**Trap:** fixing the symptom so the repro passes while the cause survives. Keep the repro tight enough that only a
real fix turns it green.

---

## 2. Spec-Driven Remediation

**For:** bringing a system up to a specification — including one you reverse-engineer from current behavior.

**Shape:**
1. **Reverse-spec** — write down what the system *should* do (from docs, intent, or observed-correct behavior).
2. **Derive failing tests** — encode the spec as checks; the gaps fail today.
3. **Fix** — implement against the failing tests, smallest increments first.
4. **Verify** — the derived tests pass; nothing previously green regresses.
5. **Persist** — record the spec and the pass/fail ledger to canonical state.

**Atoms:** Goal = "system conforms to spec S." State = the spec + a per-requirement pass/fail ledger.
**Verifier = the derived test suite** (external). Stop = all spec tests green, or a requirement is blocked →
flag for human.

**Trap:** a vague spec produces an ungated loop. If a requirement can't be expressed as a check, it isn't part of
the loop — route it to a human.

---

## 3. Performance Optimization

**For:** making something measurably faster, smaller, or cheaper without changing behavior.

**Shape:**
1. **Baseline** — measure the current metric under a fixed, repeatable benchmark. Set a target.
2. **Profile** — find the dominant cost (hotspot), don't guess.
3. **Optimize** — change one thing aimed at that hotspot.
4. **Benchmark-verify** — re-measure: did the metric improve **and** do correctness tests still pass?
5. **Keep or revert** — accept only changes that move the metric with zero behavior regression. Log.

**Atoms:** Goal = "metric M ≤ target T, behavior unchanged." State = benchmark history + accepted/reverted log.
**Verifier = benchmark hits target AND correctness suite passes** (two external gates). Stop = target met, or
diminishing returns (K iterations with no material gain).

**Trap:** chasing a faster number while silently breaking behavior. The correctness gate is non-negotiable and
runs every iteration alongside the benchmark.

---

## 4. Hybrid

**For:** real-world work that mixes the above — e.g., "fix this perf bug to spec": reproduce (MORTY) → conform to
the intended contract (Spec-Driven) → hit the latency target (Performance).

**Shape:** sequence or nest the relevant patterns. Each sub-loop keeps its own verifier; the outer loop's verifier
is the **composite** — all sub-gates green.

**Atoms:** Goal = the combined objective. State = a unified ledger across sub-loops. **Verifier = composite gate**
(every sub-verifier passes). Stop = composite green, or any sub-loop hits its safety limit.

**Trap:** letting one sub-loop's green masquerade as the whole. "Done" requires *every* gate, not the easiest one.

---

## Choosing fast

| If the task is… | Use | The verifier is… |
|-|-|-|
| A known bug to kill | MORTY | A reproduction test |
| "Make it behave correctly / to spec" | Spec-Driven | Derived spec tests |
| "Make it faster / cheaper" | Performance | Benchmark target + correctness suite |
| Several of the above at once | Hybrid | All sub-gates (composite) |

Across all four: the verifier is **external**, the state is **durable**, the stop has a **safety limit**, and the
**maker never grades its own work**.

## Verifier shape is a separate axis

A pattern picks the *work*; it does **not** pick the verifier's *shape* or when the loop stops. Those are
orthogonal — set them from the route, not the pattern:

- **gate** — one-time pass/fail (the default: recurring, MORTY, spec-driven, performance against a fixed target).
- **ratchet** — "no worse than a committed baseline", paired with a **budget** stop. For the persistent / Ralph
  case: drive a metric with no terminal "done" (`verifier.shape: ratchet` + `stop.budget`).
- **critic-panel** — k-of-N independent critics scoring against a rubric, judge ≠ maker. For subjective quality you
  can *examine* (`verifier.kind: critic-panel` + `panel`).

The [Decision Gate](decision-gate.md) routes a passing request to the archetype that sets these. Don't force every
loop into the one-shot gate — and don't fold the verifier shape into the work pattern.
