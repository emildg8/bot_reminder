# Stars: благодарность автору

**Дата:** 2026-06-04 · v3.44.4

Добровольные чаевые через Telegram Stars — **не** подписка, **не** лимиты.

## Пользователь

- `/thanks` · `/support` · кнопка **⭐ Поддержать автора** в «⋯ Ещё»
- Presets: 25 / 50 / 100 / 250 / 500 ⭐ (настраивается)
- **✨ Своя сумма** — ввод числа; фраза с буквами (например «завтра созвон») → напоминание; «abc» → ошибка, режим остаётся
- После валидной суммы — confirm «✅ Отправить N ⭐»; invoice только после подтверждения
- Invoice **всегда в личку** (в группе — подсказка «отправлен в личку»)
- После оплаты — «Спасибо, {имя}!», «⭐ Поддержать ещё»
- Nudge после «Готово»: личка, ≥3 закрытых; «Не сейчас» → `tip_nudge_dismissed_at` в БД
- `/status` — «Поддержать автора: /thanks»

## Включение

```env
STARS_TIPS_ENABLED=true
STARS_TIP_PRESETS=25,50,100,250,500
STARS_TIP_MIN=1
STARS_TIP_MAX=2500
STARS_TIPS_NOTIFY_ADMIN=true
STARS_TIP_NUDGE_ENABLED=true
STARS_TIP_NUDGE_DAYS=14
STARS_TIP_NUDGE_MIN_DONES=3
STARS_TIP_NUDGE_ONCE=true
```

BotFather → Payments → Telegram Stars.

## Smoke

```bash
python scripts/smoke_stars.py
```

1. `/thanks` → preset → оплата
2. «Своя сумма» → `75` → confirm → invoice в личку
3. «Своя сумма» → «abc» → ошибка, режим остаётся
4. «Своя сумма» → «завтра созвон» → напоминание, не Stars
5. «✅ Готово» ×3+ → nudge (если не платил)
6. Admin panel → Stars + топ 7d / 30d

## Миграции

`alembic upgrade head`:

- `20260604_0005` — `users.tip_nudge_at`
- `20260604_0006` — `users.tip_nudge_dismissed_at`

## Убрано

- Pro / Free лимиты, `/subscribe`, `/grantpro`, `/revokepro`

Legacy колонки `users.is_pro` остаются в БД, не используются.
