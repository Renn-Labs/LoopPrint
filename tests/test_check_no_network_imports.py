"""Tests for check-no-network-imports.py — the self-authored regression guard for Looptimal's
own zero-network-calls claim (item 4). Proves it catches a real injected network import, not
just that it passes trivially against the current clean repo."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check-no-network-imports.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_no_network_imports", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


checker = _load()


def test_real_repo_scripts_and_templates_are_clean():
    violations = checker.scan([REPO / "scripts", REPO / "templates"])
    assert violations == {}


def test_catches_a_direct_network_import(tmp_path):
    (tmp_path / "bad.py").write_text("import socket\n")
    violations = checker.scan([tmp_path])
    assert list(violations.keys()) == [tmp_path / "bad.py"]
    assert violations[tmp_path / "bad.py"] == {"socket"}


def test_catches_a_from_import_of_a_network_module(tmp_path):
    (tmp_path / "bad.py").write_text("from urllib.request import urlopen\n")
    violations = checker.scan([tmp_path])
    assert "urllib" in violations[tmp_path / "bad.py"]


def test_ignores_a_network_module_name_mentioned_only_in_a_string_or_comment(tmp_path):
    (tmp_path / "clean.py").write_text(
        '"""This docstring mentions socket and requests but imports neither."""\n'
        "# import socket -- commented out, must not be flagged\n"
        "x = 'requests'\n"
    )
    assert checker.scan([tmp_path]) == {}


def test_pyyaml_is_explicitly_allowed(tmp_path):
    (tmp_path / "uses_yaml.py").write_text("import yaml\n")
    assert checker.scan([tmp_path]) == {}


def test_main_exits_nonzero_on_violation(tmp_path, capsys):
    (tmp_path / "bad.py").write_text("import requests\n")
    rc = checker.main([str(tmp_path)])
    assert rc == 1
    assert "RED" in capsys.readouterr().err


def test_main_exits_zero_on_clean_dir(tmp_path, capsys):
    (tmp_path / "clean.py").write_text("import json\n")
    rc = checker.main([str(tmp_path)])
    assert rc == 0
    assert "GREEN" in capsys.readouterr().out
