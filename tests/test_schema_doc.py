"""Structural sync guard for the published schema (#8).

references/schema.md is the human-readable index of the *executable* schema (loopprint-lint.py).
These tests fail the build if the doc drifts from the linter's accepted values — so the published
contract can't silently rot away from what the linter actually enforces. Structure, not prose.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = (ROOT / "references" / "schema.md").read_text(encoding="utf-8")
SCHEMA_L = SCHEMA.lower()
LINT = ROOT / "scripts" / "loopprint-lint.py"


def _lint_mod():
    spec = importlib.util.spec_from_file_location("loopprint_lint", LINT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = _lint_mod()


def test_schema_doc_lists_all_patterns():
    for p in L.VALID_PATTERNS:
        assert p in SCHEMA, f"schema.md missing pattern value: {p}"


def test_schema_doc_lists_all_verifier_shapes():
    for s in L.VALID_VERIFIER_SHAPES:
        assert s in SCHEMA, f"schema.md missing verifier.shape value: {s}"


def test_schema_doc_lists_all_stage_success():
    for s in L.VALID_STAGE_SUCCESS:
        assert s in SCHEMA, f"schema.md missing stage_success value: {s}"


def test_schema_doc_lists_all_checkpoint_modes():
    for m in L.VALID_CHECKPOINT_MODES:
        assert m in SCHEMA, f"schema.md missing checkpoint_mode value: {m}"


def test_schema_doc_states_current_schema_version():
    v = L.SCHEMA_VERSION
    assert f"schema_version: {v}" in SCHEMA or f"`{v}`" in SCHEMA, (
        f"schema.md does not state the current SCHEMA_VERSION ({v})"
    )


def test_schema_doc_names_lint_as_executable_schema():
    # The doc must point at the linter as the enforced source of truth, not duplicate it.
    assert "loopprint-lint" in SCHEMA_L
    assert "executable schema" in SCHEMA_L


def test_schema_doc_publishes_emit_consume_contract():
    assert "emit" in SCHEMA_L and "consume" in SCHEMA_L, "emit/consume contract missing"
    assert "ralph" in SCHEMA_L, "the /ralph-emits-spec reference is missing"


def test_schema_doc_is_honest_about_no_consumer_path():
    # The deferred/hedge scope must stay explicit so the doc can't oversell a non-existent integration.
    assert (
        "defensive" in SCHEMA_L
        or "no external consumer" in SCHEMA_L
        or "no consumer path" in SCHEMA_L
    ), "schema.md must state the honest (no-consumer-path) scope"
