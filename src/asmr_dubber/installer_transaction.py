"""Recoverable source/environment replacement; large model downloads stay resumable."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import uuid
from contextlib import nullcontext
from pathlib import Path

from .platforms import portable_home
from .storage import atomic_write_text, exclusive_file_lock
from .task_control import terminate_process_tree

PRESERVED = {"checkpoints", "user-state", ".repair-state.json"}


def _target(path: Path) -> Path:
    expected = portable_home().resolve() / "runtimes" / "index-tts-2.5"
    if path.is_symlink() or path.resolve() != expected:
        raise ValueError("Refusing runtime replacement outside the IndexTTS-2.5 directory")
    return expected


def _clear_source(root: Path) -> None:
    root = _target(root)
    for child in root.iterdir():
        if child.name in PRESERVED:
            continue
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def recover(root: Path) -> None:
    root = _target(root)
    marker = root / ".repair-state.json"
    if not marker.is_file():
        return
    state = json.loads(marker.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("phase") not in {
        "backing-up",
        "installing",
        "restoring",
    }:
        raise ValueError("Invalid repair journal")
    names = state.get("names")
    if (
        not isinstance(names, list)
        or any(
            not isinstance(name, str)
            or not name
            or name in {".", ".."}
            or Path(name).name != name
            or "/" in name
            or "\\" in name
            or ":" in name
            or name in PRESERVED
            for name in names
        )
        or len(names) != len(set(names))
    ):
        raise ValueError("Invalid repair backup entries")
    backup = Path(state["backup"])
    if (
        backup.parent.resolve() != root.parent
        or not backup.name.startswith(".index-tts-2.5-backup-")
        or backup.is_symlink()
        or not backup.is_dir()
    ):
        raise ValueError("Invalid repair backup path")
    if state.get("phase") == "installing":
        _clear_source(root)
        state["phase"] = "restoring"
        atomic_write_text(marker, json.dumps(state))
    for name in names:
        if Path(name).name != name or name in PRESERVED:
            raise ValueError("Invalid repair backup entry")
        saved = backup / name
        if saved.exists():
            destination = root / name
            if destination.exists():
                raise ValueError(f"Repair recovery conflict: {destination}")
            saved.rename(destination)
    marker.unlink()
    backup.rmdir()


def run_transaction(root: Path, command: list[str]) -> int:
    root = _target(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = (
        nullcontext()
        if os.getenv("ASMR_DUBBER_INSTALL_LOCK_HELD") == "1"
        else exclusive_file_lock(portable_home() / ".runtime-install.lock")
    )
    with lock, exclusive_file_lock(root.parent / ".index-tts-2.5-repair.lock"):
        recover(root)
        backup = root.parent / f".index-tts-2.5-backup-{uuid.uuid4().hex}"
        backup.mkdir()
        names = [child.name for child in root.iterdir() if child.name not in PRESERVED]
        state = {"backup": str(backup), "names": names, "phase": "backing-up"}
        marker = root / ".repair-state.json"
        atomic_write_text(marker, json.dumps(state))
        try:
            for name in names:
                (root / name).rename(backup / name)
            state["phase"] = "installing"
            atomic_write_text(marker, json.dumps(state))
            env = os.environ.copy()
            env["ASMR_DUBBER_REPAIR_CHILD"] = "1"
            process = subprocess.Popen(command, env=env, start_new_session=os.name != "nt")
            try:
                code = process.wait()
            except BaseException:
                terminate_process_tree(process)
                raise
            if code:
                recover(root)
                return code
            marker.unlink()
            # Keep the previous environment recoverable; never silently delete it.
            print(f"Previous runtime backup retained: {backup}", flush=True)
            return 0
        except BaseException:
            recover(root)
            raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("installer command required")
    return run_transaction(args.runtime, command)


if __name__ == "__main__":
    raise SystemExit(main())
