#!/usr/bin/env python3
"""looptimal-persona-promote.py — promote a proven Tier-B synthesized persona (Agent Foundry
Dynamism) into a permanent, reusable Tier-A persona (Agent Foundry Consistency), at project or
user scope. See references/agent-foundry.md #9.

Promotion is a content REWRITE, not a file copy: a Tier-B persona (templates/agent-persona.md)
is heavily mission-bound by design ({mission-context}, {success-criteria} embed THIS run's
objective/task-node/criterion IDs); a curated persona (personas/*.md) has zero mission-specific
content. This script cannot do that rewrite for you -- only a human or the AI in-session,
looking at what the persona actually did well this mission, can generalize it responsibly. What
this script CAN do mechanically:

  --draft-from <tier-b-persona.md> --capability <slug>
      Extracts the reusable parts of a rendered Tier-B persona (its Anti-patterns and
      Pre-action-checklist sections) and prints a skeleton in the curated personas/ shape, with
      [FILL IN: ...] markers for the sections a Tier-B persona has no equivalent for (Identity,
      Core Capabilities, Failure Mode I Own). Never writes to disk.

  <slug> <finished-persona-path> [--scope project|user] [--write] [--force]
      Validates a FINISHED candidate against the curated personas/ format (checks derived
      directly from personas/architect.md and personas/security.md) and, with --write, persists
      it to personas/<slug>.md (project) or ~/.looptimal/personas/<slug>.md (user). Dry-run
      (validate + print the would-be target path, no write) is the default -- same convention
      as loopprint-skillify.py's --write flag.

Exit 0 = GREEN (validated, and written if --write). Exit 1 = RED (findings printed) or refused
(existing target without --force). Exit 2 = usage error. Stdlib-only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "Core Capabilities",
    "Failure Mode I Own",
    "Anti-Patterns to Avoid",
    "Checklist I Apply",
]

IDENTITY_RE = re.compile(r"^\*\*Identity:\*\*\s+\S")
FAILURE_MODE_RE = re.compile(r"^\*\*[^*]+\*\*\s+—\s+\S")
CHECKLIST_ITEM_RE = re.compile(r"^\d+\.\s+\S")
BULLET_ITEM_RE = re.compile(r"^[-*]\s+\S")
PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z][a-zA-Z0-9_-]*\}")
FILL_IN_RE = re.compile(r"\[FILL IN\b")
MISSION_SPECIFIC_RE = re.compile(
    r"\b([Cc]\d+|[Tt]-\d+|[Tt]ask[-_]?[Nn]ode\w*|criterion[-_]?id)\b"
)
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

TIER_B_SECTION_RE = re.compile(
    r"^##\s+(.+?)\s*$", re.MULTILINE
)


def _split_sections(text: str) -> tuple[list[str], dict[str, str]]:
    """Returns (header titles in order, {title: body}) for every '## Title' section."""
    matches = list(TIER_B_SECTION_RE.finditer(text))
    order: list[str] = []
    bodies: dict[str, str] = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        order.append(title)
        bodies[title] = text[start:end].strip("\n")
    return order, bodies


def validate_persona(text: str) -> list[str]:
    """Returns findings; empty list = GREEN. Checks derived verbatim from
    personas/architect.md and personas/security.md -- both share this exact shape."""
    findings: list[str] = []
    lines = text.splitlines()

    if not lines or not lines[0].startswith("# "):
        findings.append("missing H1 title as the first non-blank line (e.g. '# Data Engineer')")

    order, bodies = _split_sections(text)

    if order != REQUIRED_SECTIONS:
        findings.append(
            f"section headers must be exactly {REQUIRED_SECTIONS!r} in that order, got {order!r}"
        )
    else:
        preamble = text.split("## Core Capabilities", 1)[0]
        if not any(IDENTITY_RE.match(ln.strip()) for ln in preamble.splitlines()):
            findings.append(
                "missing a '**Identity:** ...' line before the first '## Core Capabilities' section"
            )

        for section in ("Core Capabilities", "Anti-Patterns to Avoid"):
            body_lines = [ln for ln in bodies[section].splitlines() if ln.strip()]
            if not body_lines:
                findings.append(f"'## {section}' has no content")
            elif not all(BULLET_ITEM_RE.match(ln.strip()) for ln in body_lines):
                findings.append(f"'## {section}' must be a bullet list (every line starts with '- ')")

        fm_lines = [ln for ln in bodies["Failure Mode I Own"].splitlines() if ln.strip()]
        if len(fm_lines) != 1 or not FAILURE_MODE_RE.match(fm_lines[0].strip()):
            findings.append(
                "'## Failure Mode I Own' must be exactly one line: '**Named Failure Mode** — description'"
            )

        cl_lines = [ln for ln in bodies["Checklist I Apply"].splitlines() if ln.strip()]
        if not cl_lines:
            findings.append("'## Checklist I Apply' has no content")
        elif not all(CHECKLIST_ITEM_RE.match(ln.strip()) for ln in cl_lines):
            findings.append("'## Checklist I Apply' must be a numbered list (every line starts with '1.', '2.', ...)")

    ph = PLACEHOLDER_RE.findall(text)
    if ph:
        findings.append(f"unfilled template placeholder(s) still present: {sorted(set(ph))!r}")

    if FILL_IN_RE.search(text):
        findings.append("unfinished '[FILL IN ...]' marker(s) still present -- this looks like a "
                         "draft-from skeleton that was never completed")

    ms = MISSION_SPECIFIC_RE.findall(text)
    if ms:
        findings.append(
            f"looks like mission-specific reference(s) survived promotion (heuristic, verify by "
            f"eye): {sorted(set(m if isinstance(m, str) else m[0] for m in ms))!r}"
        )

    return findings


def _normalize_as_checklist(body: str) -> str:
    """Mechanical only: renumber an existing numbered/bulleted list; otherwise wrap the raw
    text as a single numbered item so a human has something concrete to split up."""
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return "1. [FILL IN: no checklist content found in the source persona]"
    items: list[str] = []
    for ln in lines:
        stripped = re.sub(r"^(\d+\.|[-*])\s+", "", ln)
        items.append(stripped)
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def _normalize_as_bullets(body: str) -> str:
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return "- [FILL IN: no anti-patterns content found in the source persona]"
    items: list[str] = []
    for ln in lines:
        stripped = re.sub(r"^(\d+\.|[-*])\s+", "", ln)
        items.append(stripped)
    return "\n".join(f"- {item}" for item in items)


def draft_from(tier_b_path: Path, capability: str) -> str:
    text = tier_b_path.read_text(encoding="utf-8")
    _, bodies = _split_sections(text)
    anti_patterns = bodies.get("Anti-patterns (do not)", "")
    checklist = bodies.get("Pre-action checklist", "")

    title = capability.replace("-", " ").title()
    return f"""# {title}

**Identity:** [FILL IN: one-sentence, first-person framing of this domain expert's role -- \
what does it own, in general, beyond this one mission?]

## Core Capabilities
- [FILL IN: 4-8 general capability bullets -- generalize from what this persona actually did \
well this mission, not from the mission's specific task list]

## Failure Mode I Own
**[FILL IN: Named Failure Mode]** — [FILL IN: one-sentence description of the failure mode \
this expert specifically guards against, independent of this mission]

## Anti-Patterns to Avoid
{_normalize_as_bullets(anti_patterns)}

## Checklist I Apply
{_normalize_as_checklist(checklist)}
"""


def _target_path(scope: str, slug: str) -> Path:
    if scope == "project":
        repo_root = Path(__file__).resolve().parent.parent
        return repo_root / "personas" / f"{slug}.md"
    return Path.home() / ".looptimal" / "personas" / f"{slug}.md"


def promote(slug: str, candidate_path: Path, scope: str, write: bool, force: bool) -> int:
    if not SLUG_RE.match(slug):
        print(f"RED: slug {slug!r} must be kebab-case (lowercase letters, digits, hyphens)")
        return 1

    text = candidate_path.read_text(encoding="utf-8")
    findings = validate_persona(text)
    target = _target_path(scope, slug)

    if findings:
        print("RED")
        for f in findings:
            print(f"RED: {f}")
        return 1

    print("GREEN\ncandidate persona matches the curated personas/ format")
    print(f"target: {target}")

    if not write:
        print("(dry run -- pass --write to persist)")
        return 0

    if target.exists() and not force:
        print(f"REFUSE  {target} already exists -- pass --force to overwrite")
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"WROTE {target}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Promote a Tier-B synthesized persona into the curated personas/ library."
    )
    sub = ap.add_subparsers(dest="mode")

    draft = sub.add_parser("draft-from", help="Print a mechanical draft skeleton (stdout only)")
    draft.add_argument("tier_b_path", type=Path, help="Path to a rendered Tier-B persona.md")
    draft.add_argument("--capability", required=True, help="capability-id or domain-slug")

    promote_ap = sub.add_parser("promote", help="Validate a finished candidate and optionally persist it")
    promote_ap.add_argument("slug", help="capability-id or domain-slug (kebab-case)")
    promote_ap.add_argument("candidate_path", type=Path, help="Path to the finished persona.md candidate")
    promote_ap.add_argument("--scope", choices=["project", "user"], default="project")
    promote_ap.add_argument("--write", action="store_true", help="Persist (default: dry-run/validate only)")
    promote_ap.add_argument("--force", action="store_true", help="Overwrite an existing target")

    args = ap.parse_args(argv[1:] if argv is not None else None)

    if args.mode == "draft-from":
        if not args.tier_b_path.is_file():
            ap.error(f"{args.tier_b_path}: not a file")
        sys.stdout.write(draft_from(args.tier_b_path, args.capability))
        return 0

    if args.mode == "promote":
        if not args.candidate_path.is_file():
            ap.error(f"{args.candidate_path}: not a file")
        return promote(args.slug, args.candidate_path, args.scope, args.write, args.force)

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
