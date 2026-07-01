"""Tests for examples/critic-panel/calibration/ — proves the calibration mechanism (item 12)
both accepts an honest judge and catches a broken/lazy one, mirroring the tamper-to-RED pattern
used throughout this repo's other selftests."""
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CALIBRATION = REPO / "examples" / "critic-panel" / "calibration"
CHECK = CALIBRATION / "check_calibration.sh"


def _bash_ok() -> bool:
    """Same check as tests/test_runner_ratchet.py: the GitHub windows-latest runner ships
    bash.exe as the WSL launcher stub with no distro installed. Skip on Windows CI instead of
    failing spuriously."""
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
    not _bash_ok(), reason="judge-calibration check needs a POSIX bash (skipped on Windows CI)"
)


def test_honest_judge_passes_calibration():
    result = subprocess.run(["bash", str(CHECK)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "GREEN" in result.stdout
    assert "3/3 agree" in result.stdout


def test_broken_always_high_judge_fails_calibration(tmp_path):
    broken = tmp_path / "broken_judge.sh"
    broken.write_text(textwrap.dedent("""\
        #!/usr/bin/env bash
        echo '{"score": 90, "reason": "always confident, never actually reads the artifact"}'
    """))
    broken.chmod(0o755)

    result = subprocess.run(["bash", str(CHECK)], capture_output=True, text=True,
                            env={**os.environ, "JUDGE": str(broken)})
    assert result.returncode == 1
    assert "FAIL" in result.stderr
    assert "fail-1.md: expected=fail actual=pass" in result.stderr


def test_calibration_check_fails_loudly_on_empty_golden_set(tmp_path):
    empty_manifest = tmp_path / "expected.txt"
    empty_manifest.write_text("# nothing here\n")
    (tmp_path / "judge_under_test.sh").write_text("#!/usr/bin/env bash\necho '{}'\n")
    (tmp_path / "judge_under_test.sh").chmod(0o755)

    script = CHECK.read_text().replace(
        'GOLDEN_DIR="$(dirname "$0")/golden"', f'GOLDEN_DIR="{tmp_path}"')
    local_check = tmp_path / "check.sh"
    local_check.write_text(script)
    local_check.chmod(0o755)

    result = subprocess.run(["bash", str(local_check)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "empty golden set" in result.stderr
