#!/usr/bin/env python3
"""Smoke Stars tips: парсинг суммы, bounds, passthrough (без pytest).

Запуск: python scripts/smoke_stars.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.services.stars_tips import (  # noqa: E402
    is_tip_payload,
    is_valid_tip_amount,
    looks_like_reminder_phrase,
    looks_like_tip_amount,
    parse_tip_amount_input,
    parse_tip_payload,
    pre_checkout_error,
    text_has_letters,
    tip_payload,
)


def _ok(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def main() -> int:
    errors: list[str] = []

    for raw, want in (("75", 75), ("75 ⭐", 75), ("1 000", 1000), ("100 stars", 100)):
        got = parse_tip_amount_input(raw)
        if got != want:
            errors.append(f"parse_tip_amount_input({raw!r}) = {got}, want {want}")

    _ok(text_has_letters("завтра созвон"), "text_has_letters missed cyrillic", errors)
    _ok(looks_like_tip_amount("75"), "looks_like_tip_amount(75) false", errors)
    _ok(not looks_like_tip_amount("завтра"), "looks_like_tip_amount(phrase) should be false", errors)
    _ok(
        looks_like_reminder_phrase("завтра созвон") and not looks_like_reminder_phrase("abc"),
        "looks_like_reminder_phrase",
        errors,
    )
    _ok(is_valid_tip_amount(50) and not is_valid_tip_amount(0), "is_valid_tip_amount bounds", errors)

    p = tip_payload(42, 100)
    _ok(parse_tip_payload(p) == (42, 100), f"parse_tip_payload roundtrip {p}", errors)
    _ok(is_tip_payload(p), "is_tip_payload(tip) false", errors)
    _ok(not is_tip_payload("other:1"), "is_tip_payload(other) should be false", errors)
    _ok(
        pre_checkout_error(p, payer_id=42, total_amount=100) is None,
        "pre_checkout_error valid tip",
        errors,
    )
    _ok(
        pre_checkout_error(p, payer_id=99, total_amount=100) is not None,
        "pre_checkout_error wrong user",
        errors,
    )

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK smoke_stars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
