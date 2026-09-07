import importlib.util
import zipfile
from pathlib import Path


def test_inventory_records_actual_wheels_and_hashes(tmp_path):
    path = Path(__file__).parents[1] / "scripts/export-dependency-inventory.py"
    spec = importlib.util.spec_from_file_location("dependency_inventory", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    wheel = tmp_path / "example-1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "example-1.0.dist-info/METADATA",
            "Name: example\nVersion: 1.0\nLicense-Expression: MIT\nRequires-Dist: other>=1\n",
        )
    records = module.inventory(tmp_path)
    assert len(records) == 1
    assert records[0]["name"] == "example"
    assert records[0]["license"] == "MIT"
    assert records[0]["requires_dist"] == ["other>=1"]
    assert len(records[0]["sha256"]) == 64
