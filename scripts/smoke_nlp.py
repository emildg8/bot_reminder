#!/usr/bin/env python3
"""Smoke NLP: ключевые фразы после деплоя (без pytest).

Запуск: python scripts/smoke_nlp.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.services.nlp.ambiguous_time import (  # noqa: E402
    detect_ambiguous_day_hour,
    detect_ambiguous_day_only,
)
from bot.services.nlp.rule_parser import parse_with_rules  # noqa: E402

TZ = "Europe/Moscow"

CASES: tuple[tuple[str, dict], ...] = (
    ("сегодня через 1 минуту тест", {"kind": "once", "delay": 60, "text": "тест"}),
    ("завтра через 2 дня оплатить", {"kind": "once", "delay": 172800, "text": "оплатить"}),
    ("завтра в 2 дня созвон", {"kind": "once", "text": "созвон", "hour": 14}),
    ("завтра каждые 2 часа встать", {"kind": "interval", "interval": 7200, "text": "встать"}),
)


def _check(phrase: str, expect: dict) -> list[str]:
    errors: list[str] = []
    parsed = parse_with_rules(phrase, TZ)
    if parsed is None:
        return [f"{phrase!r}: parse returned None"]
    if parsed.kind != expect["kind"]:
        errors.append(f"{phrase!r}: kind={parsed.kind}, want {expect['kind']}")
    if parsed.text != expect["text"]:
        errors.append(f"{phrase!r}: text={parsed.text!r}, want {expect['text']!r}")
    if "delay" in expect and parsed.delay_seconds != expect["delay"]:
        errors.append(
            f"{phrase!r}: delay={parsed.delay_seconds}, want {expect['delay']}"
        )
    if "interval" in expect and parsed.interval_seconds != expect["interval"]:
        errors.append(
            f"{phrase!r}: interval={parsed.interval_seconds}, want {expect['interval']}"
        )
    if "hour" in expect and parsed.run_at.hour != expect["hour"]:
        errors.append(f"{phrase!r}: hour={parsed.run_at.hour}, want {expect['hour']}")
    if detect_ambiguous_day_only(phrase) or detect_ambiguous_day_hour(phrase):
        errors.append(f"{phrase!r}: unexpected ambiguous prompt")
    return errors


def main() -> int:
    errors: list[str] = []
    for phrase, expect in CASES:
        errors.extend(_check(phrase, expect))
    if errors:
        print("smoke_nlp FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"smoke_nlp OK · {len(CASES)} phrases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
