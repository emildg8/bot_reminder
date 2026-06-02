#!/usr/bin/env python3
"""Проверка ops-артефактов перед деплоем."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SMOKE_ENV = {
    **os.environ,
    "BOT_TOKEN": os.environ.get("BOT_TOKEN") or "0:ci-test-token",
}
REQUIRED = (
    "README.md",
    "CHANGELOG.md",
    "start.sh",
    ".github/DEPLOY.md",
    "docs/guides/ops-checklist.md",
    "bot/main.py",
    "bot/version.py",
    "pyproject.toml",
    "alembic.ini",
    "alembic/env.py",
    "alembic/versions/20260531_0001_initial_schema.py",
    "bot/db/migrate.py",
    "scripts/smoke_stars.py",
    "scripts/smoke_group_mentions.py",
    "scripts/smoke_nlp.py",
    "scripts/check_deploy.py",
    "docker-compose.yml",
)


_SMOKE_SCRIPTS = (
    "smoke_nlp.py",
    "smoke_group_mentions.py",
    "smoke_stars.py",
)


def _run_smoke_scripts() -> list[str]:
    errors: list[str] = []
    for name in _SMOKE_SCRIPTS:
        path = ROOT / "scripts" / name
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            env=_SMOKE_ENV,
        )
        if proc.returncode != 0:
            tail = (proc.stdout or "") + (proc.stderr or "")
            errors.append(f"{name} failed (exit {proc.returncode}): {tail.strip()[-200:]}")
    return errors


def _read_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError(f"no version in {path}")
    return match.group(1)


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            errors.append(f"missing file: {rel}")

    if not (ROOT / "start.sh").read_text(encoding="utf-8").strip().startswith("#!/"):
        errors.append("start.sh should be a bash script")

    start_sh = (ROOT / "start.sh").read_text(encoding="utf-8")
    if "python -m bot.main" not in start_sh:
        errors.append("start.sh must run python -m bot.main")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    if "LOCAL_WHISPER_ENABLED=false" not in env_example:
        errors.append(".env.example should default LOCAL_WHISPER_ENABLED=false")

    ver_py = _read_version(ROOT / "bot" / "version.py")
    ver_toml = ROOT / "pyproject.toml"
    if f'version = "{ver_py}"' not in ver_toml.read_text(encoding="utf-8"):
        errors.append(f"version mismatch: bot/version.py={ver_py} vs pyproject.toml")

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.doc_metrics import verify_doc_test_counts, verify_doc_version

    errors.extend(verify_doc_version(ROOT, ver_py))
    errors.extend(verify_doc_test_counts(ROOT))
    errors.extend(_run_smoke_scripts())

    if errors:
        print("verify_ops FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"verify_ops OK · v{ver_py}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
