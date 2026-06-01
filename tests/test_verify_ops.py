
from scripts.verify_ops import ROOT, _read_version, main


def test_verify_ops_passes():
    assert main() == 0


def test_version_files_in_sync():
    ver = _read_version(ROOT / "bot" / "version.py")
    toml = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{ver}"' in toml
