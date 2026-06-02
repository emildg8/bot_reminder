# Stars: благодарность автору

**Дата:** 2026-06-03 · v3.43.0

Добровольные чаевые через Telegram Stars — **не** подписка, **не** лимиты.

## Пользователь

- `/thanks` · `/support` · кнопка **⭐ Поддержать автора** в «⋯ Ещё»
- Presets: 50 / 100 / 250 ⭐ (настраивается)
- После оплаты — «Спасибо!», функции не меняются

## Включение

```env
STARS_TIPS_ENABLED=true
STARS_TIP_PRESETS=50,100,250
STARS_TIPS_NOTIFY_ADMIN=true
```

BotFather → Payments → Telegram Stars.

## Smoke

1. `/thanks` → кнопки сумм
2. Оплата → «Спасибо! ⭐ …»
3. Admin panel → «Stars: N · сумма …»

## Убрано

- Pro / Free лимиты, `/subscribe`, `/grantpro`, `/revokepro`

Legacy колонки `users.is_pro` остаются в БД, не используются.
