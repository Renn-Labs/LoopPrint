# Looptimal Roadmap

**Snapshot date:** 2026-06-30 (day of the v2.0.0 tag, pre-announcement). Not sealed, not a Looptimal
mission — this is a strategic planning artifact, produced and reviewed like any other doc PR. Revisit
it each time a horizon empties or the market signal below goes stale (external framework/tooling facts
move fast; re-check before trusting a citation more than a few months old).

---

## Status reconciliation (2026-07-01)

Verified directly against `main` (code and tests read, not inferred from this doc's own prose) — not
trusted blindly. This block is purely additive: nothing below was deleted or rewritten. Where an
item's original prose makes a present-tense claim the current repo state now contradicts, a bracketed
`[Correction 2026-07-01: …]` is appended inline right after that sentence, so the original reasoning
stays legible as a historical record rather than being silently edited away.

**Shipped on `main` (12 of 14 — items 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14):**

- **1 — Zero-clone quickstart.** `pyproject.toml` exists with a working `[project.scripts]` block
  (`looptimal-doctor`, `looptimal-lint`, `verify-outcome`, etc.) delegating to `scripts/*.py`.
- **2 — Demo asset.** `assets/demo.gif` and `assets/demo.cast` both exist.
- **3 — README overhaul.** The first screen has the zero-clone proof block ("Prove it in under a
  minute"), three badges (CI, license, GitHub stars), and the three sourced numbers (SpecBench
  arXiv:2605.21384, ImpossibleBench arXiv:2510.20270, Cursor's SWE-bench Pro study) in place of the
  old first-principles-only argument.
- **5 — SSH-signed release tags.** Cryptographically confirmed, not just documented: `git -c
  gpg.ssh.allowedSignersFile=allowed_signers.example tag -v v2.0.0` returns `Good "git" signature for
  …`. `RELEASE.md` documents the process and `allowed_signers.example` ships at the repo root.
- **7 — HMAC-keyed hash-pin.** `scripts/_common.py::canonical_contract_hash()` now accepts optional
  `key` (HMAC-SHA256) and `sealed_dir` (full sealed-tree materials-folding) parameters, and both are
  wired into the real verification paths in `verify-outcome.py` and `looptimal-lint.py` (opt-in via a
  configured framer key; the old unkeyed self-digest stays the default when no key is set, for
  backward compatibility). **Confirmed absent at the `v2.0.0` tag commit** via `git show
  <tag-commit>:scripts/_common.py` (no `hmac`/`sealed_dir_materials` hits) — it landed in a later
  commit (`20a32d2`, after the tag). Not yet in any release tag.
- **8 — Checker-only visibility tier.** `templates/contract.yaml` has
  `criteria[].visibility: maker-visible | checker-only` (default `maker-visible`);
  `scripts/looptimal-lint.py` enforces it and emits the soft "zero checker-only criteria" advisory
  for `sensitivity: high` missions. (`references/schema.md` documents `loop-spec.yaml` /
  `campaign-spec.yaml` / `verifier-library.yaml` only — it never covered `contract.yaml` fields even
  before this shipped, so its silence on `visibility` isn't a documentation regression.)
- **9 — Dagger Container-Use isolation recipe.** `examples/dagger-isolation/README.md` exists and
  documents the pattern with an illustrative `profile.yaml` snippet. **Caveat, self-disclosed in the
  file's own "Status" section:** "documentation of a pattern, not a shipped, tested integration —
  Dagger is never imported by any `scripts/*.py` file, and no CI job in this repo exercises
  Container-Use." Counted as shipped (the example/profile the item asked for exists) but it is docs,
  not a tested integration — flagging this so the distinction isn't lost.
- **10 — Hard-vs-soft gate labeling.** `templates/verifier-library.yaml` has `gate_type: hard | soft`
  on every recipe, cross-referenced from `looptimal-lint.py` and `contract.yaml`.
- **11 — Structured critic verdicts.** `examples/critic-panel/critic-1.sh` now outputs
  `{"score": 90, "reason": "..."}` (structured JSON), not a bare integer.
- **12 — Judge-calibration recipe.** `tests/test_judge_calibration.py` and
  `examples/critic-panel/calibration/check_calibration.sh` both exist.
- **13 — Cross-Provider Judge Quorum oracle.** `references/oracle-library.md` pattern #14 is live.
- **14 — Sealed Tool-Trajectory Match oracle.** `references/oracle-library.md` pattern #15 is live,
  backed by `templates/tool_trajectory_check.py`. The library now totals 15 patterns (was 13).

**Still open (2 of 14 — items 4, 6) — do not treat as shipped:**

- **4 — Independent, CI-gated skill-audit badge.** **Not wired.** `.github/workflows/ci.yml` has no
  audit-related job (only `test`, `runner-smoke`, `shellcheck`, `lint-specs`,
  `version-consistency`, `no-network-imports`); `README.md` still shows only 3 badges (CI, license,
  stars) — no audit badge. `CONTRIBUTING.md` is explicit that the closest existing thing
  (`scripts/check-no-network-imports.py`) is "a self-authored regression guard, not an independent
  third-party audit — we'd welcome a PR wiring in a genuinely independent skill-auditing tool if a
  stable one turns up." Genuinely open.
- **6 — Marketplace/awesome-list listings.** No evidence of submission to `awesome-claude-code`,
  `awesome-claude-skills`, or `anthropics/claude-plugins-official` anywhere in the repo or git log.
  The only related hits are `CHANGELOG.md` references to the pre-existing self-hosted `renn-labs`
  marketplace, which is the status quo the item itself describes as insufficient, not a new listing.
  Launch-phase work, not yet executed, as expected.

**Release-tag gap.** None of the shipped code/doc work above (items 1, 2, 3, 7-14) is reflected in a
git release tag yet — `v2.0.0` is the latest tag and predates all of it (directly confirmed for item
7; the rest ship after the same tag by the same evidence — a 2026-06-30-dated roadmap describing them
as still-to-do, now present on `main`). Item 5 is the one exception: SSH tag signing is a property of
the `v2.0.0` tag itself, already verified above. Closing the rest of this gap is the job of a planned
**v2.1.0** release — a separate task, not in scope here.

---

## How this was built

Two passes, kept separate on purpose (the project's own maker-≠-checker instinct applied to itself):

1. **Internal audit** — full read of `README.md`, `CHANGELOG.md`, `RELEASE.md`, `SECURITY.md`,
   `CONTRIBUTING.md`, `release-boundary.md`, `references/*.md`, the plugin manifest, all 5 open GitHub
   issues, merged PR history, and prior `.omc/` planning artifacts (including the original 2026-06-26
   feature analysis, most of which has since shipped).
2. **External research** — six parallel research agents, each given the internal findings as ground
   truth and one distinct lens (competitive landscape; spec-driven-development & reward-hacking
   discourse; the Claude Code/MCP ecosystem; eval/LLM-judge tooling; supply-chain attestation; OSS
   launch playbooks), each required to cite a real, current source per claim.

Two load-bearing claims from the research pass were re-verified directly against this repo's source
before being trusted: the sealed-contract hash **is** confirmed to be an unkeyed `sha256` self-digest
over the contract mapping only (`scripts/_common.py::canonical_contract_hash`, no folding-in of
`sealed/` file contents) — that finding stands. A second claim, that the critic-panel `PROVIDER=`
lint advisory was phantom/unimplemented, was **checked and found false** — it's real and wired up in
`scripts/loopprint-lint.py` (`_PROV_RE`, ~line 165, advisory at ~line 278); the claim came from grepping
the wrong linter file (the outcome-layer `looptimal-lint.py` instead of the loop-spec-layer
`loopprint-lint.py`). Dropped from this roadmap accordingly. Treat every other external citation below
as sourced-but-not-independently-verified — good enough to plan against, not good enough to assert as
fact in marketing copy without a second look.

## How to read this

Three horizons, not a strict priority stack — ranking 20 items 1-to-20 with false precision would be
its own kind of overclaiming. Each item names what it is, why it's here (internal gap, named backlog,
or external signal), and a rough impact/effort read (1-5, solo-maintainer-effort-scaled). Bundled items
say so explicitly rather than padding the count.

- **Horizon 1 — Now.** Directly touches the open item on the release-boundary checklist: the public
  announcement hasn't happened yet (4 stars, 6 days old). These are the cheapest, highest-leverage
  things to land *before or right at* that moment.
- **Horizon 2 — Next.** Hardens the actual moat — sealed verification, maker ≠ checker — where research
  found the sharpest, most concrete gaps (several verified directly against this repo's own source).
- **Horizon 3 — Later.** Ecosystem reach, the remaining named backlog, and work explicitly gated on a
  trigger condition the maintainer already stated (build it *when*, not *now*).

---

## Horizon 1 — Now: launch readiness

### 1. Zero-clone quickstart (`pyproject.toml` + console-scripts + `uvx --from git+...`)
Re-scopes open issue #9 ("packaged CLI") into a much smaller first slice. No `pyproject.toml` exists in
the repo today, so this is unscoped work, not a restatement of the issue. [Correction 2026-07-01:
`pyproject.toml` now exists on main, with a working `[project.scripts]` block wired to `looptimal_cli`
(which delegates to `scripts/*.py`) — see `pyproject.toml`.] A `[project.scripts]` block
wired to the existing `scripts/looptimal-doctor.py` etc. needs no PyPI account, no name-squatting risk,
no trusted-publishing setup — but it gives a first-time visitor one copy-pasteable command
(`uvx --from git+https://github.com/Renn-Labs/Looptimal looptimal-doctor`) that runs the tool without a
clone, the same mechanic that makes `npx vercel` convert. Pin the README example to a tagged ref, not
`@main`. Stdlib-only wrapper — imports the existing scripts, adds no runtime dependency.
*Impact 5 / Effort 2.*

### 2. Record the real demo asset — lead with tamper-to-RED, not a feature tour
Sharpens issue #7. No new content needs authoring: `examples/critic-panel/run_demo.sh` and
`scripts/verify-outcome.py --selftest` already script a PASS-then-intentional-fail-flip / tamper-to-RED
sequence — record that, not a happy path. It's Looptimal's actual differentiator (an outer verifier
catching a self-reported GREEN as fraudulent) and it's the specific kind of provable claim a skeptical
technical audience rewards over sales language. Use `agg` (the current asciinema-to-GIF standard;
`asciicast2gif` is archived) against a disposable tmpdir. Keep it under ~20 seconds.
*Impact 5 / Effort 2.*

### 3. README overhaul: hoist the proof, add true badges, cite the research
Three changes to one file, sequenced together because they all touch the first screen: (a) move a
zero-clone proof block (once #1 exists) above the philosophy/pipeline table — onboarding research is
specific that conversion tracks literal seconds-to-first-proof, and today nothing zero-clone is
documented at all [Correction 2026-07-01: README.md now leads with a "Prove it in under a minute"
zero-clone proof block above the pipeline table — see README.md.]; (b) add three *objectively true,
re-checkable* badges (CI status, license, star count) — the repo already runs a full
Ubuntu/macOS/Windows CI matrix with shellcheck and a version-consistency gate, and currently shows
zero badges for any of it [Correction 2026-07-01: README.md now shows three badges — CI, license,
GitHub stars — at the top of the file.]; (c) replace the first-principles
argument for maker ≠ checker with three sourced numbers now available: SpecBench's finding that the
visible-vs-holdout-test pass-rate gap grows ~28 points per 10x increase in code size (arXiv:2605.21384),
ImpossibleBench's finding that hiding tests drops cheating from up to 76% to near zero (arXiv:2510.20270),
and Cursor's finding that 63% of "successful" SWE-bench Pro resolutions were retrieved from git
history/the web rather than derived. No unverifiable claims (no "production ready," no synthetic
counters) — stay inside the project's own honest-gates voice. *Impact 4 / Effort 1.*

### 4. Independent, CI-gated skill-audit badge
2026 produced third-party auditors built specifically because Claude Code skills run with full system
permissions by default — the open-source, no-account **Skill Safety Auditor** (14 checks: credential
access, outbound network calls, shell commands, source provenance) is a close-to-exact match for what
`SECURITY.md` already *asserts* about this project (stdlib-only, zero network calls in core) but has
never had independently checked. Wiring one into CI so a regression (a stray network call creeping into
`scripts/*.py`) fails the build, then showing the badge next to the "126 passing tests" line, turns an
asserted differentiator into a verified one. This is the one self-referential move the project's own
invariants actually allow — a separately-built third party doing the checking is genuine maker ≠
checker, not the rejected "Looptimal verifying Looptimal" meta-loop. Pick the free/local-runnable
tool, not a paid tier, so the badge doesn't become a budget dependency of the release process.
*Impact 5 / Effort 2.*

### 5. Sign release tags with SSH
Every other hardening item here protects a *generated* loop's sealed contract or a future packaged CLI —
today the only install path is git clone or manual copy, and nothing lets a user verify a checkout
actually came from Renn Labs unmodified. [Correction 2026-07-01: the `v2.0.0` tag is now SSH-signed
and independently verifies — `git tag -v v2.0.0` (with `allowed_signers.example` configured) returns
`Good "git" signature for …` — see `RELEASE.md` and `allowed_signers.example`.] GitHub verifies
SSH-signed tags/commits natively (Git 2.34+,
no keyserver, reuses an existing push key) and marks them "Verified." A few `git config` lines and
`git tag -s` on the next tag — no new dependency. Document this in `RELEASE.md` as *release hygiene*,
distinct from the sealed-contract hash-pin work in Horizon 2 — different guarantee, don't conflate them.
*Impact 3 / Effort 1.*

### 6. List where Claude Code users actually look
Today Looptimal ships only from its own self-hosted `renn-labs` marketplace — reachable only by someone
who already has the GitHub URL. `anthropics/claude-plugins-official` is now the default `/plugin`
Discover-tab surface and explicitly accepts third-party submissions via a public form, judged on
docs/security/scope, not star count. Cross-list on `awesome-claude-code` and `awesome-claude-skills`
(both plain PR-to-add, no application) at the same time — near-zero effort, pure documentation PRs.
Sequence this **after** items 2-4 land, so the first review/impression is a working demo and a visible
CI badge, not a bare repo. Submission outcome and timing are Anthropic's call, not the maintainer's —
treat this as "submit and wait," not a guaranteed ship date. *Impact 4-5 / Effort 1-2.*

---

## Horizon 2 — Next: harden the verification core

This is where the roadmap earns its keep — the actual moat is the sealed suite and maker ≠ checker, and
research (cross-checked against the live source) found the sharpest gaps here.

### 7. Harden the sealed-contract hash-pin (the #1 maintainer-named future item, made concrete)
Confirmed by reading `scripts/_common.py` directly: `canonical_contract_hash()` is an **unkeyed**
`sha256` self-digest over the parsed `contract.yaml` mapping — anyone who can write the sealed contract
can recompute the same hash after editing it. Two concrete, code-verified sub-fixes: (a) swap it for an
**HMAC-SHA256** keyed digest — Python stdlib has no asymmetric signing (`hashlib`/`hmac`/`secrets` give
hashing, a symmetric MAC, and a CSPRNG, nothing more), but that's exactly enough for a keyed digest: a
random 32-byte key from `secrets.token_bytes(32)`, stored outside every executor-writable root, checked
with `hmac.compare_digest()`; (b) **extend the hash to cover the full `sealed/` directory tree**, not
just `contract.yaml` — today the oracle scripts a criterion's `external_check` actually invokes (e.g.
`sealed/check_repro.py`) are protected *only* by `is_sealed()`'s filesystem-permission check, zero
cryptographic binding to the contract hash. In-toto calls this "materials": fold a sorted
`{relpath: sha256}` map of `sealed/` into the same digest so editing an oracle script without touching
`contract.yaml` now fails verification instead of silently passing. Needs a migration note for the 8
shipping examples (their `contract_hash` values change) and a lockstep lint update so CI catches drift
immediately. Document the key-custody boundary as honestly as the current residual is documented today —
this closes it, doesn't eliminate all trust assumptions. *Impact 5 / Effort 3.*

### 8. Checker-only ("holdout") visibility tier in the acceptance-suite schema
`references/simulate.md` already names a "holdout oracle" as Stage-4 red-team advice — but it's prose,
not schema. `contract.yaml` has no visibility field, so nothing enforces it. [Correction 2026-07-01:
`templates/contract.yaml` now has `criteria[].visibility: maker-visible | checker-only` (default
`maker-visible`), enforced by `scripts/looptimal-lint.py` including the soft zero-checker-only-criteria
advisory for `sensitivity: high` missions described two sentences below.] This is the single
highest-value gap 2026 reward-hacking research points at directly: SpecBench (arXiv:2605.21384) defines
reward hacking as exactly the visible-vs-holdout pass-rate gap; ImpossibleBench (arXiv:2510.20270) found
hiding tests is what actually collapses cheating, not just mutating them. Add
`criteria[].visibility: maker-visible | checker-only` (default `maker-visible`, fully backward
compatible). Stage 5 Execute context-assembly shows checker-only criteria only their `id`/`category`,
never `oracle`/`external_check`/`green_means` text; Stage 6 still runs all criteria regardless.
`looptimal-lint.py` adds a **soft** warning (never a REJECT — REJECT stays reserved for the Tier-0
loop-worthiness gate) when a `sensitivity: high` mission ships zero checker-only criteria. Needs a
documented override for missions where full maker visibility is intentional (e.g. Supervised archetype).
*Impact 5 / Effort 2.*

### 9. Optional Dagger Container-Use isolation recipe
The disclosed residual in `SECURITY.md` is that anti-tamper trust rests on OS filesystem permissions
plus the checker controlling `--workdir`. Dagger open-sourced close to the missing piece in 2026:
"Container-Use" gives each agent its own isolated, git-branch-backed container that runs identically
locally and in CI. An optional example profile that runs the Execute-stage maker and the
Verify-outcome-stage checker in separate containers turns maker ≠ checker from a convention into
something infrastructure-enforced — strictly opt-in, ships as an example/profile, never a core
dependency (preserves zero-runtime-dependency-core and zero-network-in-core). Complements #7; this
hardens execution isolation, #7 hardens spec integrity — different failure modes. *Impact 4 / Effort 2.*

### 10. Hard-vs-soft gate labeling in the verifier cookbook
The closest competitive "verified agent" toolkit found in research (Microsoft's ASSERT/Agent Control
Specification, MIT-licensed, ~4.5k stars, launched 2026-03) is confirmed — by direct inspection of its
own docs — to be LLM-judge policy scoring with **no deterministic verification mode at all**. Add
`gate_type: hard | soft` to `templates/verifier-library.yaml`, a recipe wiring an external eval harness
(ASSERT/DeepEval/promptfoo-style) as a labeled **soft** gate, and a Verify-outcome-stage rule that
refuses to certify success without at least one **hard** gate present. This is maker ≠ checker enforced
one level deeper than any competitor found in this research currently does — it stops an LLM-judge-only
check from silently passing as if it were a real test/build/repro gate. External harnesses get invoked
as a subprocess the sealed suite shells out to, never a Python import — consistent with the existing
"never `eval()` a parsed command string" rule. *Impact 5 / Effort 2.*

### 11. Structured `{score, reason}` critic verdicts
Confirmed directly: `examples/critic-panel/critic-1.sh` does `echo 90` — a bare integer, explicitly
commented "Output integer only," with zero rationale. [Correction 2026-07-01:
`examples/critic-panel/critic-1.sh` now outputs structured JSON —
`{"score": 90, "reason": "..."}` — not a bare integer.] Every major eval framework checked (promptfoo's
`llm-rubric`, DeepEval's G-Eval) returns a reason alongside the score specifically so boundary failures
are debuggable — the verifier-library's own existing caveat ("re-run on boundary cases") is
undercut without one. Extend the critic stub contract to `{score, reason}` and have `verify.sh` JSON-escape
the reason field properly (via a one-line `python3 -c json.dumps` call, not naive string interpolation —
free-text model output with quotes/newlines will otherwise corrupt `critics.jsonl`). *Impact 3 / Effort 1.*

### 12. Judge-calibration recipe
Both the `llm-rubric-judge` and critic-panel recipes carry a "judge inconsistency is real" caveat today
with no mechanism to check it. [Correction 2026-07-01: a calibration mechanism now exists —
`examples/critic-panel/calibration/check_calibration.sh` and `tests/test_judge_calibration.py`.] Anthropic's own eval guidance treats calibrating a judge against
human-labeled examples as load-bearing, not optional. A bounded, stdlib-only addition: a template of
5-10 `(artifact, expected-verdict)` pairs plus a small harness that runs a critic script against each and
requires a minimum agreement rate before the loop trusts it. Document it honestly as "catches a broken or
lazy judge (always scores 90, ignores the rubric)," not as statistically rigorous calibration — a 5-10
example set is a smoke test, not proof of scoring accuracy. *Impact 4 / Effort 3.*

### 13. Promote judge-based scoring to a first-class oracle: #14 "Cross-Provider Judge Quorum"
`references/oracle-library.md` has 13 sealed, lint-bindable patterns; none is a first-class binding
target for an open-ended/subjective criterion (a written artifact, a design doc, a research brief) even
though the mechanism to seal one — `rubric_sha`, judge roster, `quorum_k`, threshold — already exists in
`verifier-library.yaml`'s critic-panel recipe and is proven end-to-end in `examples/critic-panel/`.
[Correction 2026-07-01: `references/oracle-library.md` now has pattern #14 "Cross-Provider Judge
Quorum" — this gap is closed.] This
is a promotion, not new infrastructure: give it a number, the same sealing discipline as the other 12
(rubric/roster/quorum frozen before Execute), and an explicit lint rule that the sealed judge roster may
not include any provider matching the maker's provider. *Impact 4 / Effort 2.*

### 14. New oracle pattern: #15 "Sealed Tool-Trajectory Match"
All 13 existing oracle patterns verify final state or output; none verifies the Execute-stage agent's
*process* — which tools it called, in what order, whether it stayed inside an allowed/forbidden list.
[Correction 2026-07-01: `references/oracle-library.md` now has pattern #15 "Sealed Tool-Trajectory
Match", implemented via `templates/tool_trajectory_check.py` — this gap is closed. The library now
totals 15 patterns.]
A maker that used a forbidden write-access tool to fabricate its own passing state is a real, currently
unaddressed failure mode. LangChain's `agentevals` ships exactly this (`create_trajectory_match_evaluator`,
strict/unordered/subset modes) as a deterministic, LLM-free evaluator category, distinct from
output-quality checks. Scriptable in pure stdlib Python by diffing a sealed allow/deny/order list against
a tool-call transcript — real prerequisite: needs a stable, parseable transcript format, which likely
differs per harness (Claude Code vs. OpenCode vs. Hermes, etc.), so a per-profile normalization step needs
scoping as part of this, not assumed to already exist. *Impact 4 / Effort 3.*

---

## Horizon 3 — Later: ecosystem reach & long tail

### 15. Phase-2 crypto: provenance sidecar + optional signing + PyPI attestations
Three related, smaller follow-ons once #7 ships and proves out: (a) an optional
`sealed/provenance.intoto.jsonl` — adopting the in-toto/SLSA Statement JSON *shape* (not its heavy
reference tooling, which pulls in `securesystemslib` + `cryptography`/`cffi` and would break the
stdlib-only core) so the provenance claim is interoperable with tools people already trust, honestly
describable as SLSA "Build L1" (self-describing, unsigned) without ever claiming Sigstore-grade
assurance; (b) a strictly optional Ed25519 upgrade for third parties who shouldn't need to hold an HMAC
secret to verify — shell out to `minisign` (a single small offline binary, no daemon, no transparency
log) if present on `PATH`, exactly as optional as the existing PyYAML dependency; (c) once the CLI
packaging item is actually PyPI-published, turn on PyPI's PEP 740 Sigstore-backed build attestations via
GitHub Actions Trusted Publishing — default-on, zero new runtime dependency, protects the *distribution*
channel rather than the sealed contracts Looptimal generates for users. Ship only if something will
actually read the sidecar — an unused attestation is ceremony. *Impact 3-4 / Effort 2-3 each.*

### 16. Verifier-library recipe pack: OWASP Agentic Top-10 + reward-hack-resistant recipes
Sharpens the already-open issue #5 ("grow the verifier-library cookbook") with a concrete shape instead
of restating it. OWASP's Top 10 for Agentic Applications 2026 (ASI01-ASI10: goal hijack, tool misuse,
privilege abuse, supply-chain compromise, unexpected code execution, memory/context poisoning, insecure
inter-agent comms, cascading failures, human-trust exploitation, rogue agents) is now the taxonomy
serious evaluators grade against (the UK AI Safety Institute's own 2026 standard uses it directly) — a
themed, deterministic-where-possible recipe batch, one per category, buys instant credibility with
security-conscious adopters via a citable standard instead of ad hoc gates. Pair with a smaller
"reward-hack-resistant" family named by Shihab et al.'s 2026 taxonomy and Cursor's own findings:
`monkeypatch-guard` (re-exec the oracle in a fresh subprocess instead of trusting an in-process object
the maker's code could have mutated — the exact technique METR found o3/Claude 3.7 Sonnet exploiting) and
`provenance-flag` (a soft Stage-6 advisory, never a hard block, that flags a fetch-then-byte-identical-diff
pattern in `tool_receipts[]`). Content-heavy — scope as an incremental multi-release addition, not one
drop, and keep every recipe genuinely scriptable, not a dressed-up LLM-judge checklist (would undercut
item #10's hard/soft distinction). *Impact 3 / Effort 3.*

### 17. Spec-driven-development interop: optional `.specify/`/`.kiro/` ingestion + EARS-informed lint
Two small, related pieces from the same research thread. GitHub's spec-kit (`.specify/memory/constitution.md`,
`specs/<feature>/spec.md`, v0.11.0 as of mid-2026, 30+ agent integrations) and AWS Kiro
(`.kiro/steering/*.md`, `.kiro/specs/*/requirements.md` in EARS notation, launched internationally
May 2026) are now common in repos Looptimal gets pointed at — and independent 2026 coverage confirms
neither verifies generated code against a live running app, leaving the same agent session that wrote
the code to judge it against a spec it "may have internalized." That's exactly the gap Stage 6 exists to
close, which is worth stating plainly if this ships. (a) An optional Stage-0 Frame helper that, if either
tool's artifacts exist in the target repo, surfaces them as candidate objective/acceptance-criteria text
for a human to accept or edit — never auto-sealed, saves re-typing without weakening the sealed suite's
authority; must stay a pure content-ingestion helper and never touch `looptimal-detect.py`'s harness
resolution. (b) An EARS-informed lint pass flagging vague/unmeasurable phrasing ("should," "may,"
"appropriate") in `green_means`/`external_check` text — cheap, stdlib regex catalog, warnings only, never
a REJECT. *Impact 3 / Effort 1-2.*

### 18. Optional groundedness/citation-fidelity oracle recipe
Nothing today checks whether an artifact's *cited claims* are actually true — the rubric/critic-panel
recipes score writing quality, not source-fidelity, and Braintrust's `autoevals` library deliberately
splits "faithfulness" (matches the source) from "factuality" (is it true) as two distinct scorer types
for exactly this reason. For any research-report-style Looptimal loop, a fluent, well-organized artifact
with fabricated citations passes every existing gate today. This is the one recipe that necessarily makes
outbound network calls (fetching cited URLs), so it ships as an opt-in snippet, not core — consistent
with the existing precedent that `critic-N.sh` already dispatches to live LLM CLIs. Needs a distinct
"citation unreachable" exit condition, separate from "citation contradicts artifact," or link rot
produces false REDs and erodes trust in the gate. *Impact 3 / Effort 2.*

### 19. Expose doctor/lint/verify as direct callable surfaces
Two related discovery levers, bundled because both are "stop making people reach for prose or a bash
block to use tooling that already works": (a) thin `commands/*.md` slash-command wrappers around
`looptimal-doctor.py`/`looptimal-lint.py`/`verify-outcome.py` — 2026's plugin.json formalizes `commands/`
as tab-completable and independently discoverable from `skills/`, regardless of whether the model's
semantic match against the long `SKILL.md` description fires; (b) an optional, strictly read/verify-only
stdio MCP adjunct exposing the same two tools to any MCP-speaking host, not just SKILL.md-compatible
harnesses — MCP is now the dominant cross-agent interop layer (10k+ indexed servers, governance under the
Linux-Foundation-backed Agentic AI Foundation as of Dec 2025). Both must stay pure delegating wrappers
with zero logic duplication — the four already-tested Python entry points stay the single source of
truth — and the MCP surface specifically must stay scoped to read/verify only: 2026 security research
(OX Security, April) names STDIO MCP servers combining a persistent process, shell access, and no auth
layer as a real vulnerability class. *Impact 3-4 / Effort 2-3.*

### 20. Long-tail backlog & trigger-gated work
Smaller already-tracked items, bundled here because none individually justifies its own release, plus
one item that's explicitly *not ready yet* by the maintainer's own stated rule:
- **Missing harness profiles** — ship `profiles/codex.example.yaml` and `profiles/grok-build.example.yaml`
  to match the two harnesses the README already claims manual-install support for but which have no
  example profile today (5 of 7 claimed harnesses do).
- **`loopprint-*` → `looptimal-*` rename** with compat shims — already flagged in `CONTRIBUTING.md` as a
  candidate for "a future minor release," not urgent, don't do it ad hoc inside an unrelated PR.
- **`loopprint ls --global`** cross-repo portfolio view (issue #8).
- **An `update` helper** for copy-based installs (issue #6).
- **Tier-0 decision-gate `--explain-only`** — export the existing Tier-0 "is this even a loop" verdict as
  a standalone, transparent markdown scorecard. (CrewAI's 2026 "Discovery" feature — a proprietary,
  cloud-side, pattern-matched version of the same "should you automate this" question — is independent
  market validation that this category is real and wanted; Looptimal's version stays a transparent rubric
  applied to stated criteria, not a trained recommender, and should say so.)
- **`run-campaign.sh`** — the general multi-stage campaign orchestrator, intentionally deferred today
  (`references/campaign.md`). Build it once the maintainer's own two stated conditions are both true:
  script-level maker ≠ checker lint is GREEN (already true) **and** a real supervised harness asks for it
  (not yet true). Don't build ahead of that signal.

*Impact 2-3 / Effort 1-3 depending on the sub-item.*

---

## What's deliberately not here

No hosted SaaS dashboard, no cloud telemetry, no proprietary "smart" recommender to compete with
CrewAI Discovery on its own terms — all would cut against the zero-network-in-core / stack-agnostic-core
invariants this roadmap was built to respect. Anything here that later turns out to need one should be
shipped as a clearly optional adjunct (same pattern as PyYAML today), never folded into the core.
