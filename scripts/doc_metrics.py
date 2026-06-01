"""Сверка числа тестов в docs с фактическим pytest --collect-only."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

# collect-only импортирует handlers → Settings(); как в CI pytest
_COLLECT_ENV = {**os.environ, "BOT_TOKEN": os.environ.get("BOT_TOKEN", "0:ci-test-token")}

# (путь относительно root, regex с одной группой — число тестов)
DOC_TEST_COUNT_CHECKS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("README.md", re.compile(r"\*\*(\d+) тест(?:а|ов)\*\*")),
    ("docs/guides/quality-metrics.md", re.compile(r"## (\d+) тест(?:а|ов) \(pytest\)")),
    ("docs/guides/quality-metrics.md", re.compile(r"## Карта тестов \((\d+)\)")),
    ("docs/v1.0-final-status.md", re.compile(r"passed \(\*\*(\d+)\*\*\)")),
    ("docs/plans/improvements-plan-2026-06.md", re.compile(r"(\d+) тест")),
    ("docs/plans/product-audit-2026.md", re.compile(r"\*\*(\d+)\*\* тест(?:а|ов)")),
)


def pytest_collect_count(root: Path, *, timeout: float = 120.0) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=_COLLECT_ENV,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    match = re.search(r"(\d+) tests? collected", combined)
    if proc.returncode != 0 or not match:
        raise RuntimeError(
            f"pytest --collect-only failed (exit {proc.returncode}): {combined[-500:]}"
        )
    return int(match.group(1))


def verify_doc_test_counts(root: Path, expected: int | None = None) -> list[str]:
    """Вернуть список ошибок; пустой список — всё совпало."""
    if expected is None:
        expected = pytest_collect_count(root)

    errors: list[str] = []
    for rel, pattern in DOC_TEST_COUNT_CHECKS:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing file for test count check: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        match = pattern.search(text)
        if not match:
            errors.append(f"{rel}: pattern {pattern.pattern!r} not found")
            continue
        found = int(match.group(1))
        if found != expected:
            errors.append(f"{rel}: docs={found}, pytest collected={expected}")
    return errors


def verify_doc_version(root: Path, version: str) -> list[str]:
    errors: list[str] = []
    docs_readme = root / "docs/README.md"
    if docs_readme.is_file():
        text = docs_readme.read_text(encoding="utf-8")
        if f"**v{version}**" not in text:
            errors.append(f"docs/README.md: expected **v{version}** in header")
    readme = root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        if f"[v{version}]" not in text and f"v{version}" not in text:
            errors.append(f"README.md: expected v{version} in version line")
    return errors
