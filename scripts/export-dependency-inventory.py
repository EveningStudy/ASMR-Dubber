"""Inventory the actual wheel archives included in a portable distribution."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from email.parser import BytesParser
from pathlib import Path


def inventory(wheelhouse: Path) -> list[dict[str, object]]:
    records = []
    for wheel in sorted(wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(wheel) as archive:
            members = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(members) != 1:
                raise ValueError(f"Invalid wheel metadata: {wheel.name}")
            metadata = BytesParser().parsebytes(archive.read(members[0]))
        with wheel.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        records.append(
            {
                "name": metadata["Name"],
                "version": metadata["Version"],
                "license": metadata.get("License-Expression") or metadata.get("License", "unknown"),
                "requires_dist": metadata.get_all("Requires-Dist", []),
                "archive": wheel.name,
                "size": wheel.stat().st_size,
                "sha256": digest,
            }
        )
    if not records:
        raise ValueError("No wheels found")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheelhouse", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = {
        "schema": 1,
        "scope": "bundled wheel archives; not isolated model runtimes",
        "packages": inventory(args.wheelhouse),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
