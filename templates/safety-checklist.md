# Safety checklist — <slug>

Confirm before any autonomous run. A loop with authority and no guardrails is the failure mode this skill exists
to prevent.

## Stop conditions are real
- [ ] **Safety limit set** — `max_iterations` and/or a token/time budget in `loop-spec.yaml`.
- [ ] **Halt path works** — touching `loops/<slug>/HALT` stops the loop within one iteration.
- [ ] **Success is objective** — the verifier, not the maker, decides "done".

## Irreversibility is gated
- [ ] **Every irreversible action is a human checkpoint** (not an autonomous step): deletes, pushes/merges,
      deploys, payments, external sends, credential or infra changes.
- [ ] **Blast radius is bounded** — runs in a branch / worktree / sandbox / dry-run first, not straight on `main`
      or production.
- [ ] **Rollback exists** — you can undo a bad iteration (VCS, snapshot, backup).

## Maker ≠ checker
- [ ] The verifier is **external** and the reviewer (if any) is a **different** agent/process than the maker.
- [ ] Each iteration logs a state change **and** a verifier result.
- [ ] **Cross-provider (advisory)** — run `loopprint-detect.py` / `loopprint-doctor.py` to see `provider.available`; if 2+ agent CLIs are listed, point `dispatch.checker` at a different one than `dispatch.maker` (strongest maker≠checker). Not required: with one or zero providers, a deterministic gate (tests/lint) or the same CLI in a separate role is sufficient.

## Budget & cost
- [ ] Token / wall-clock budget is set and you're willing to spend it.
- [ ] You're tracking **cost-per-accepted-change**, not just iteration count.

## Secrets & data
- [ ] No credentials, keys, or private data in the loop's prompts, state file, or logs.
- [ ] External calls (if any) only send what they must.

## Human awareness
- [ ] Someone will see the result (notification / report) — the loop isn't silently autonomous forever.
- [ ] For unattended runs: an explicit end (success, limit, or halt) is guaranteed.
