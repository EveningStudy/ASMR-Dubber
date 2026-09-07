from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from asmr_dubber.installer_transaction import recover, run_transaction


def runtime(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("ASMR_DUBBER_HOME", str(tmp_path))
    monkeypatch.delenv("ASMR_DUBBER_INSTALL_LOCK_HELD", raising=False)
    root = tmp_path / "runtimes/index-tts-2.5"
    root.mkdir(parents=True)
    (root / "old.py").write_text("old")
    (root / "checkpoints").mkdir()
    (root / "checkpoints/model").write_text("weights")
    return root


def test_failed_install_restores_source_and_keeps_downloads(tmp_path, monkeypatch):
    root = runtime(tmp_path, monkeypatch)
    code = (
        "from pathlib import Path; import sys; r=Path(sys.argv[1]); "
        "(r/'new.py').write_text('new'); "
        "(r/'checkpoints'/'partial').write_text('resume'); sys.exit(4)"
    )
    assert run_transaction(root, [sys.executable, "-c", code, str(root)]) == 4
    assert (root / "old.py").read_text() == "old"
    assert not (root / "new.py").exists()
    assert (root / "checkpoints/partial").read_text() == "resume"
    assert not (root / ".repair-state.json").exists()


def test_success_keeps_recoverable_previous_source(tmp_path, monkeypatch):
    root = runtime(tmp_path, monkeypatch)
    assert run_transaction(root, [sys.executable, "-c", "pass"]) == 0
    backups = list(root.parent.glob(".index-tts-2.5-backup-*"))
    assert len(backups) == 1
    assert (backups[0] / "old.py").read_text() == "old"
    assert (root / "checkpoints/model").read_text() == "weights"


@pytest.mark.parametrize("phase", ["backing-up", "installing", "restoring"])
def test_interrupted_repair_recovers_idempotently(tmp_path, monkeypatch, phase):
    root = runtime(tmp_path, monkeypatch)
    backup = root.parent / ".index-tts-2.5-backup-test"
    backup.mkdir()
    (root / "old.py").rename(backup / "old.py")
    if phase == "installing":
        (root / "partial.py").write_text("partial")
    (root / ".repair-state.json").write_text(
        json.dumps({"backup": str(backup), "names": ["old.py"], "phase": phase})
    )
    recover(root)
    recover(root)
    assert (root / "old.py").read_text() == "old"
    assert not (root / "partial.py").exists()


def test_repair_rejects_broad_target(tmp_path, monkeypatch):
    monkeypatch.setenv("ASMR_DUBBER_HOME", str(tmp_path))
    with pytest.raises(ValueError):
        run_transaction(tmp_path, [sys.executable, "-c", "pass"])


def test_invalid_journal_never_deletes_current_source(tmp_path, monkeypatch):
    root = runtime(tmp_path, monkeypatch)
    backup = root.parent / ".index-tts-2.5-backup-test"
    backup.mkdir()
    (root / ".repair-state.json").write_text(
        json.dumps(
            {
                "backup": str(backup),
                "names": ["../outside"],
                "phase": "installing",
            }
        )
    )
    with pytest.raises(ValueError):
        recover(root)
    assert (root / "old.py").read_text() == "old"
