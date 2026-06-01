from pathlib import Path

from scripts.doc_metrics import verify_doc_test_counts, verify_doc_version

ROOT = Path(__file__).resolve().parent.parent


def test_doc_test_counts_match_pytest_collect():
    errors = verify_doc_test_counts(ROOT)
    assert errors == [], "\n".join(errors)


def test_doc_version_matches_bot():
    from scripts.verify_ops import _read_version

    ver = _read_version(ROOT / "bot" / "version.py")
    errors = verify_doc_version(ROOT, ver)
    assert errors == [], "\n".join(errors)
