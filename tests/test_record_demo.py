"""Smoke test for scripts/record-demo.py — confirms it produces a valid, real asciinema v2
.cast file (not that the demo LOOKS a certain way, just that the mechanism is sound)."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "record-demo.py"


def _bash_ok() -> bool:
    """record() shells out to `bash run_demo.sh` for one of its steps. Same check as
    tests/test_runner_ratchet.py: the GitHub windows-latest runner ships bash.exe as the WSL
    launcher stub with no distro installed. Skip on Windows CI instead of failing spuriously."""
    if sys.platform.startswith("win"):
        return False
    b = shutil.which("bash")
    if not b:
        return False
    try:
        out = subprocess.run([b, "-c", "echo ok"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() == "ok"
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _bash_ok(), reason="record-demo needs a POSIX bash (skipped on Windows CI)"
)


def _load():
    spec = importlib.util.spec_from_file_location("record_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_record_produces_valid_cast_with_real_captured_output(tmp_path):
    record_demo = _load()
    out_path = tmp_path / "demo.cast"
    record_demo.record(out_path)

    assert out_path.exists()
    lines = out_path.read_text().splitlines()
    assert len(lines) > 1  # header + at least one event

    header = json.loads(lines[0])
    assert header["version"] == 2

    events = [json.loads(line) for line in lines[1:]]
    assert all(len(e) == 3 and e[1] == "o" for e in events)
    timestamps = [e[0] for e in events]
    assert timestamps == sorted(timestamps)  # monotonically non-decreasing

    full_text = "".join(e[2] for e in events)
    assert "SELFTEST GREEN" in full_text  # the real verify-outcome.py --selftest output
    assert "quorum PASS" in full_text and "quorum FAIL" in full_text  # the real run_demo.sh output
