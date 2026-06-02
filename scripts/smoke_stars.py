#!/usr/bin/env python3
"""Smoke Stars tips: парсинг суммы и bounds (без pytest).

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
    looks_like_tip_amount,
    parse_tip_amount_input,
    parse_tip_payload,
    pre_checkout_error,
    text_has_letters,
    tip_payload,
)


def main() -> int:
    errors: list[str] = []

    cases = (
        ("75", 75),
        ("75 ⭐", 75),
        ("1 000", 1000),
        ("100 stars", 100),
    )
    for raw, want in cases:
        got = parse_tip_amount_input(raw)
        if got != want:
            errors.append(f"parse_tip_amount_input({raw!r}) = {got}, want {want}")

    if text_has_letters("завтра созвон"):
        pass
    else:
        errors.append("text_has_letters missed cyrillic")

    if looks_like_tip_amount("75"):
        pass
    else:
        errors.append("looks_like_tip_amount(75) false")

    if not looks_like_tip_amount("завтра"):
        pass
    else:
        errors.append("looks_like_tip_amount(phrase) should be false")

    if is_valid_tip_amount(50) and not is_valid_tip_amount(0):
        pass
    else:
        errors.append("is_valid_tip_amount bounds")

    p = tip_payload(42, 100)
    if parse_tip_payload(p) != (42, 100):
        errors.append(f"parse_tip_payload roundtrip failed for {p}")

    if not is_tip_payload(p):
        errors.append("is_tip_payload(tip) false")

    if is_tip_payload("other:1"):
        errors.append("is_tip_payload(other) should be false")

    if pre_checkout_error(p, payer_id=42, total_amount=100) is not None:
        errors.append("pre_checkout_error valid tip should be None")

    if pre_checkout_error(p, payer_id=99, total_amount=100) is None:
        errors.append("pre_checkout_error wrong user should fail")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK smoke_stars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
