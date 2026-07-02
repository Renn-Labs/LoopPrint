# Verification Receipt

A **verification receipt** is a small, public JSON file that records a single **verified outcome** —
an independently re-run, GREEN Stage-6 result — in a form a third party (or CI) can re-check from
first principles. It is deliberately *not* a badge you write by hand: a receipt is a byproduct of
`scripts/verify-outcome.py` returning GREEN against live state, and it carries the hashes and
(optionally) the keyed signature needed to prove that.

Looptimal ships **no telemetry**. The receipt is the project's honest, opt-in adoption signal: a
`looptimal-receipt.json` committed to a public repository is discoverable via GitHub code search, and
because every field re-derives from the sealed contract + evidence bundle, an observer can tell a real
receipt from a fabricated one. This page is the design spec for that file; it does not describe
implementation code (that is a separate task).

> **Core invariant.** A receipt exists only for a GREEN live re-run. It is never emitted after RED,
> never assembled from a maker's self-report, and never stands in for the evidence bundle it points
> at. The receipt records that verification *happened and passed* — not that someone *claims* it did.

## Why a fixed filename

The file MUST be named **`looptimal-receipt.json`** and live at the **repository root**, by
convention, not by configuration. This is a deliberate constraint, not an oversight:

- The receipt's job as an adoption metric depends on being **findable**. GitHub code search over a
  predictable `filename:looptimal-receipt.json` (or the in-content sentinel below) is only a coherent
  signal if every adopter uses the same name in the same place. A per-project configurable name would
  fragment the very signal the receipt exists to produce.
- A fixed root-level path is also what lets a CI workflow (a separate planned feature) locate and
  re-verify the receipt without per-repo configuration.

An emitter MAY accept an explicit output path for non-standard layouts (monorepos, examples), but the
**default and documented** location is `./looptimal-receipt.json`, and the adoption metric is defined
against that default. To keep content search robust even where the filename varies, every receipt also
carries a stable sentinel field (`"kind": "looptimal-receipt"`) that code search can match on directly.

## Schema

`schema_version: 1`. All hashes are lowercase hex; a `sha256:` prefix is tolerated on read (verifiers
normalize with `_common.normalize_hash`). The receipt is JSON (the same tiny-YAML-compatible shape the
rest of Looptimal uses via `_common.load_config`).

| Field | Type | Required | Notes |
|-|-|-|-|
| `kind` | const | yes | Always `"looptimal-receipt"`. Stable content sentinel for code search + disambiguation. |
| `schema_version` | int | yes | `1`. A verifier that understands a lower version than declared must refuse rather than guess. |
| `objective_hash` | string | yes | SHA-256 of the normalized objective text (the contract's `objective`). Opaque; safe to publish. |
| `objective` | string | no | The one-sentence normalized objective, in the clear. Opt-in — the receipt is **public**, so include only when the objective text is safe to disclose. See Limits. |
| `contract_ref` | string | yes | Repo-relative, non-traversing path to the sealed contract (mirrors the evidence bundle's `contract_ref`). Lets a verifier locate the contract to re-derive its hash. |
| `contract_hash` | string | yes | The canonical contract hash from the GREEN verdict — HMAC-SHA256 when keyed, plain SHA-256 when not. Shape is identical either way; `contract_hash_keyed` disambiguates. |
| `contract_hash_keyed` | bool | yes | `true` if `contract_hash` is a keyed HMAC digest; `false` if it is the unkeyed SHA-256 self-digest. A verifier MUST re-derive in the matching mode or the hash will never match. |
| `evidence_bundle_ref` | string | yes | Repo-relative, non-traversing path to the `evidence-bundle.json` the verdict was produced from. |
| `evidence_bundle_sha256` | string | yes | SHA-256 of the exact evidence-bundle bytes. Pins the proof the receipt summarizes. |
| `verdict` | const | yes | Always `"GREEN"`. Any other value is itself a verification failure (a receipt for a non-GREEN run must not exist). |
| `criteria_passed` | list[string] | yes | The criterion IDs that passed live, copied from the verdict's `criteria[].criterion` where `passed == true`. Because GREEN requires every sealed criterion to pass, this MUST equal the sealed suite's full criterion set — a strict subset is a verification failure. |
| `repeat` | int | yes | The quorum count (`--repeat`) the GREEN run used, copied from the verdict. A receipt from `repeat: 1` is weaker evidence than one from `repeat: 5`; verifiers MAY require a floor. |
| `toolchain` | map | yes | `{ "looptimal": "<version>", "python": "<x.y.z>" }`. `looptimal` is read from the canonical version source `.claude-plugin/plugin.json`'s `"version"` (the same source `check-version-consistency.py` guards); `python` is `platform.python_version()`. |
| `created_at` | string | yes | ISO-8601 UTC, `%Y-%m-%dT%H:%M:%SZ` — the same format the Stage-6 verdict's `ts` uses. |
| `ci_run_url` | string \| null | no | The public CI run URL when emitted in CI (e.g. derived from `GITHUB_SERVER_URL`/`GITHUB_REPOSITORY`/`GITHUB_RUN_ID`); `null`/absent for a local run. Advisory in an unkeyed receipt (hand-editable); load-bearing only when a CI re-run is what stamped it — see Trust tiers. |
| `signature` | map | conditional | Present **iff** a framer key was resolved at emission (`contract_hash_keyed == true`). Shape `{ "alg": "HMAC-SHA256", "value": "<hex>" }`, an HMAC over the canonical receipt payload (all fields except `signature`). Absent for an unkeyed receipt. |

### Skeleton (keyed)

```json
{
  "kind": "looptimal-receipt",
  "schema_version": 1,
  "objective_hash": "sha256:<hex>",
  "objective": "A cache miss for a missing project returns 404 with a structured error.",
  "contract_ref": "sealed/contract.yaml",
  "contract_hash": "<hex>",
  "contract_hash_keyed": true,
  "evidence_bundle_ref": "evidence-bundle.json",
  "evidence_bundle_sha256": "<hex>",
  "verdict": "GREEN",
  "criteria_passed": ["C1", "C2"],
  "repeat": 3,
  "toolchain": { "looptimal": "2.0.0", "python": "3.11.9" },
  "created_at": "2026-07-01T00:00:00Z",
  "ci_run_url": null,
  "signature": { "alg": "HMAC-SHA256", "value": "<hex>" }
}
```

An **unkeyed** receipt is byte-identical except `contract_hash_keyed` is `false` and the `signature`
key is omitted entirely (not `null` — absent, so it is excluded from any future signed payload without
special-casing).

## Signature canonicalization

The signature reuses `canonical_contract_hash`'s canonicalization discipline exactly — it does **not**
invent a second scheme. `canonical_contract_hash` signs `{k: v for k, v in contract.items() if k !=
"contract_hash"}`; the receipt signs the analogous payload with its own self-referential field
excluded:

1. Build the payload mapping = the full receipt **minus the `signature` field** (mirroring how the
   contract hash excludes `contract_hash`, avoiding a circular digest).
2. Serialize canonically: `json.dumps(payload, sort_keys=True, separators=(",", ":"),
   ensure_ascii=True).encode("utf-8")` — the identical serialization `canonical_contract_hash` uses, so
   ordering and separators cannot drift between the two.
3. `signature.value = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()`, where `key` comes from
   `_common.resolve_framer_key` (precedence: `--key-file`, then `LOOPTIMAL_FRAMER_KEY`; hex-decoded).
4. Verification recomputes steps 1–3 over the receipt-minus-`signature` and compares to the recorded
   `value`. Any change to any signed field — cosmetic ones like `objective` or `ci_run_url` included —
   changes the digest and fails the check.

Because the framer key is the same key that makes `contract_hash` a keyed HMAC (and, in
`verify-outcome.py`, folds the `sealed/` materials manifest into that hash via `sealed_dir_materials`),
signing `contract_hash` transitively binds the sealed oracle scripts into the receipt signature too —
there is no need to duplicate a materials manifest inside the receipt.

### The key toggles both, as a pair

Just as `verify-outcome.py` treats `key` as switching hash mode and `sealed_dir` folding together
(never one without the other), the receipt treats a resolved framer key as switching on **both** the
keyed `contract_hash` **and** the receipt `signature`. There is no valid receipt with a keyed
`contract_hash` but no signature, or vice versa; a verifier rejects that inconsistency.

## Emission semantics

A receipt is produced by (or immediately alongside) `scripts/verify-outcome.py`, from the verdict it
already computes — never as a standalone tool a maker can invoke to assert success.

1. **Only on GREEN.** Emission is gated on `verify()` returning `ok == True`. On RED, no receipt is
   written and any pre-existing receipt is left untouched (a stale GREEN receipt beside a now-RED tree
   is the verifier's problem to catch on re-check, not the emitter's to silently "fix").
2. **From the verdict, not from claims.** `contract_hash`, `criteria_passed`, and `repeat` are copied
   out of the verdict object; `evidence_bundle_sha256` is computed over the bundle bytes on disk;
   `toolchain`/`created_at` are captured at emission. No field is sourced from the maker's
   `acceptance_results` or `verifier_trace` (those can only *lose* in Stage 6, and they cannot *win*
   here either).
3. **Keyed when a key is configured.** If `resolve_framer_key` returns a key, the receipt is keyed and
   signed; otherwise it is unkeyed and unsigned, and (matching `verify-outcome.py`'s existing advisory)
   the emitter should note that an unkeyed receipt proves consistency, not authorship.
4. **Location.** Default `<workdir>/looptimal-receipt.json` (the live target repo root — the same
   `--workdir` the checks ran against, i.e. the repo an adopter commits). Note the asymmetry with the
   Stage-6 **verdict**, which `verify-outcome.py` refuses to write into the maker-writable bundle dir:
   the verdict is a *trusted gate output* that must stay out of maker reach, whereas the receipt is a
   *published record* whose credibility comes from re-derivation, not from where it sits — so writing
   it into the repo root is safe. A maker who later hand-edits the committed receipt does not gain
   anything a verifier won't catch (keyed: HMAC fails; unkeyed: see Limits).
5. **Opt-in.** Emission should be explicit (e.g. a flag), not a silent side effect of every verify run,
   so Looptimal never writes a file into a user's repo without being asked. (Default-on-for-GREEN vs.
   opt-in is flagged as an open question below.)

## Verification semantics

Re-checking a receipt is the whole point — the file only means something if an independent party can
reproduce it. The procedure (for a third party or a CI job) is:

1. Load `looptimal-receipt.json`; confirm `kind == "looptimal-receipt"`, `schema_version` is understood,
   and `verdict == "GREEN"`.
2. Resolve `contract_ref` and `evidence_bundle_ref` as repo-relative, non-traversing paths (reject
   absolute/`..` paths, as `verify-outcome.py` already does for the bundle's refs).
3. Re-derive the evidence-bundle hash: `sha256(bundle_bytes) == evidence_bundle_sha256`.
4. Re-derive the contract hash from the sealed contract on disk with `canonical_contract_hash`, in the
   mode `contract_hash_keyed` declares (keyed → pass the framer `key` and, as `verify-outcome.py` does,
   `sealed_dir=<contract dir>` + `exclude=<contract file>`; unkeyed → no key). Compare with
   `normalize_hash` for prefix tolerance.
5. **If keyed**, recompute the receipt signature (Signature canonicalization above) and compare to
   `signature.value`. A mismatch is an immediate, hard FAIL — this is what makes a keyed receipt
   unforgeable without the key.
6. **Re-run the sealed suite live** via `verify-outcome.py` against the referenced bundle/workdir. The
   run MUST return GREEN, and the set of passed criterion IDs MUST equal `criteria_passed`. The live
   re-run is authoritative; the receipt's recorded fields can only lose to it.
7. The receipt "verifies" **only if every step passes**. Any single failure is RED.

An unkeyed receipt that clears steps 1–4 and 6 proves **internal consistency** — the hashes and the
live re-run agree with each other — but it does **not** prove **authorship or authenticity**. There is
no signature to check, so someone could hand-edit an unkeyed receipt's unsigned cosmetic fields (or
author a whole `looptimal-receipt.json` by hand) and, as long as the referenced contract, bundle, and
live state genuinely re-derive, it will still "verify" locally. This is a disclosed limit, not a bug in
the check: an unkeyed receipt is a claim of consistency, and consistency is all it can be trusted to
mean. Authenticity requires either a framer key (step 5) or a CI re-run (below).

### What makes a badge trustworthy: the CI re-run

For an **external viewer** — someone who finds a `looptimal-receipt.json` in a public repo and wants to
believe it — the strongest cheap evidence is a **GitHub Actions CI re-run** (a separate planned
feature). A CI workflow that checks out the repo and runs the verification procedure above produces a
public run log that a bystander can open: the receipt was re-derived and the sealed suite re-run *in
infrastructure the repo owner does not privately control the output of*, so it cannot be locally faked
the way a hand-written JSON file can. A badge or adoption count built on **CI-verified** receipts is
therefore trustworthy in a way one built on locally-emitted receipts is not. The `ci_run_url` field
points at that log; in an unkeyed receipt the URL itself is only advisory (it's editable text), so the
trustworthy configuration is **CI that holds the framer key in secrets and emits keyed receipts** —
then the CI run both re-verifies and signs, and neither the URL nor the signature can be forged without
the key.

## Trust tiers

Receipts are not all equal evidence. Verifiers and any downstream metric should distinguish:

| Tier | What produced it | Proves | Does not prove |
|-|-|-|-|
| Unkeyed, local | `verify-outcome.py` GREEN, no framer key | Internal consistency: contract/bundle hashes + live re-run agree | Authorship/authenticity — hand-editable; anyone can author one |
| Keyed, local | GREEN + framer key (`--key-file`/`LOOPTIMAL_FRAMER_KEY`) | Consistency **and** authorship — only a key-holder could sign | That the re-run happened anywhere the observer can inspect |
| CI-verified | A CI re-run of the verification procedure (ideally keyed via CI secrets) | Consistency, authorship (if keyed), **and** that a re-run actually occurred in publicly inspectable infra | (Strongest tier this design targets) |

CI-verified receipts are **strictly stronger** than locally-emitted ones, and keyed are strictly
stronger than unkeyed. A metric that counts receipts should weight or filter by tier, not treat a
hand-authorable unkeyed file as equivalent to a CI-signed one.

## Relationship to the evidence bundle

The receipt is a compact, public, optionally-signed **pointer** to a full verification; the
`evidence-bundle.json` (see [`evidence-bundle.md`](evidence-bundle.md)) is the detailed Definition-of-Done
proof. They are complementary:

- The bundle carries the nine DoD obligations (artifacts, tool receipts, acceptance results, final-state
  assertion, unresolved risks, persisted-state ref, …) and may contain internal detail a project does
  not want to publish. The receipt carries only what is safe and useful as a public signal.
- The receipt does **not** replace the bundle. Full external re-verification (step 6) requires the
  sealed contract and the bundle to be present — which, in a CI re-run, they are, because CI checks out
  the repo. Where the bundle is *not* committed, a third party can still check the signature and
  toolchain of a keyed receipt, but cannot re-run the suite; state that dependency honestly rather than
  implying a lone receipt is self-sufficient.

## Recommended self-test (tamper-to-RED)

Following `verify-outcome.py`'s `--selftest` precedent (honest bundle → GREEN; tamper live state →
RED; keyed honest → GREEN; tamper a sealed oracle script under the hash-pin → RED), the receipt
emitter/verifier should ship a `--selftest` that proves the anti-forgery claims mechanically, not just
in prose:

1. Emit an honest keyed receipt from a GREEN run → verifier returns GREEN.
2. Hand-edit one cosmetic field (`objective` or `ci_run_url`) of the keyed receipt → signature check
   fails → RED. (Proves keyed receipts are tamper-evident.)
3. Tamper the live target state so the sealed suite no longer passes → live re-run fails → RED. (Proves
   the receipt cannot outlive the outcome it records.)
4. Emit an honest *unkeyed* receipt → verifier returns GREEN, and reports it as **consistency-only** so
   the weaker guarantee is never silently upgraded.

A receipt design that cannot demonstrate 2 and 3 has not earned the word "verification."

## Limits (honest)

Matching the project's disclosed-limits convention (see the README "Security model" section and
[`SECURITY.md`](../SECURITY.md)):

- **What a receipt proves:** that at `created_at`, on the recorded toolchain, a Stage-6 re-run against
  live state returned GREEN for the referenced sealed contract and evidence bundle, and (if keyed) that
  the receipt was signed by a holder of the framer key. Nothing more.
- **What a receipt does NOT prove:** that the outcome still holds *now* (state can regress after
  emission — re-run to know), that the objective was worth pursuing, or — for an **unkeyed** receipt —
  that any particular person authored it. An unkeyed receipt proves internal consistency, not
  authorship: because there is no signature to check, a hand-edited or hand-authored unkeyed receipt
  will still "verify" locally as long as the contract, bundle, and live state genuinely re-derive. Do
  not read an unkeyed receipt as an authenticity claim.
- **Keyed vs. unkeyed** is the same trade-off `verify-outcome.py` already documents: the unkeyed SHA-256
  path is fully backward compatible and self-consistent but forgeable by anyone who can write the files;
  the keyed HMAC path is unforgeable without the key, but only if the key genuinely lives outside
  everything the maker/CI-attacker can read (never under `sealed/`, never committed). A receipt is no
  stronger than the key discipline behind it.
- **CI-verified > locally-emitted, strictly.** A locally-emitted receipt is only as trustworthy as the
  machine that made it; a CI-verified (ideally keyed-in-CI) receipt is re-derived in publicly
  inspectable infrastructure and is the tier an external adoption metric should rest on. Do not
  over-claim that a bare committed receipt is proof of anything to a stranger — it is proof to a
  re-verifier, and the CI re-run is what turns "trust me" into "check the run log."
- **Public by design.** The receipt is meant to be committed to a public repo. Never let it carry
  secrets, credentials, internal paths, or objective text a project would not publish; the `objective`
  field is opt-in for exactly this reason, with `objective_hash` as the always-safe default.

## Open questions (resolve before implementation)

1. **`objective` default.** Publish the human-readable objective by default, or default to
   `objective_hash`-only and require opt-in for the clear text? (Leaning: hash by default, clear text
   opt-in, because the file is public.)
2. **Emission trigger.** Default-on for every GREEN run, or opt-in via an explicit `--emit-receipt`
   flag? (Leaning: opt-in, to never write into a user's repo unprompted.)
3. **CI key custody.** For trustworthy external badges, should the framer key live in CI secrets so CI
   emits **keyed** receipts, and is a plain `ci_run_url` (spoofable in an unkeyed file) acceptable in
   the interim, or should the CI feature require keyed-in-CI from day one?
4. **Metric definition.** Does the adoption count filter/weight by trust tier (unkeyed / keyed /
   CI-verified), and does it enforce a `repeat` floor? A count that treats a hand-authorable unkeyed
   file as equal to a CI-signed one reintroduces exactly the "trivially forgeable badge" risk this
   design exists to close.
5. **Version-source coupling.** Reading `looptimal` version from `.claude-plugin/plugin.json` couples the
   emitter to repo layout. Confirmed as the canonical source (`check-version-consistency.py` guards it),
   but worth a shared helper rather than re-reading the path in a second place.

## Decisions (2026-07-01)

Resolving the open questions above so implementation (`verify-outcome.py --receipt` /
`--check-receipt`) has no ambiguity left to re-litigate:

1. **`objective`:** hash-only by default. `objective_hash` is always present; the clear-text
   `objective` field is omitted unless the caller passes an explicit opt-in (e.g.
   `--receipt-include-objective`). The file is public — default to the safe side.
2. **Emission trigger:** opt-in via an explicit flag (`--receipt [path]`, default `<workdir>/
   looptimal-receipt.json` when the flag is bare). Never a silent side effect of a normal
   `verify-outcome.py` run — matches the `--write`/dry-run-default convention already used by
   `loopprint-skillify.py` and `looptimal-persona-promote.py`.
3. **CI key custody:** the GitHub Action (separate task) MUST support a keyed-in-CI mode from
   its first version — a repo secret mapped to `LOOPTIMAL_FRAMER_KEY` in the workflow env — and
   its docs must state plainly that an unkeyed CI receipt is weaker evidence (consistency only,
   same as any unkeyed receipt) even though it ran in public infrastructure. Ship both modes;
   default the documented quickstart to the keyed one.
4. **Metric definition:** a raw GitHub code-search hit count cannot distinguish trust tiers (a
   search match doesn't reveal `contract_hash_keyed` or whether it ran in CI). Until tier-aware
   counting exists, any public reporting of this number (`.omc/plans/content-queue/`, launch
   copy, README) must be phrased as *"repos containing a Looptimal receipt file"* — never as
   *"verified"* or *"proven"* repos — to avoid overclaiming what a bare count can show. A
   tier-aware metric (e.g. fetching and inspecting each hit) is a legitimate future refinement,
   not required for v1.
5. **Version-source coupling:** implementer should factor a small `read_plugin_version()` (or
   similarly named) helper into `scripts/_common.py`, used by both the receipt emitter and
   (opportunistically) `check-version-consistency.py`, rather than re-deriving the read twice.

---

Author: Renn Labs. MIT.
