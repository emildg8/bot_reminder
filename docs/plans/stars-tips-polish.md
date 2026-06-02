# План: Stars tips — polish перед продом

**Базовая версия:** v3.44.0 ✅ · **Дата:** 2026-06-04  
**Статус:** волна M закрыта в v3.44.0
**Контекст:** [stars-tips.md](../guides/stars-tips.md) · аудит «со стороны» (чат 2026-06)

## Цель

Довести благодарность Stars до **production-ready**: не ломать core-сценарий (создание напоминаний), корректно работать в любых чатах, не раздражать nudge'ом.

**Не в scope:** возврат Pro, лимиты, paywall, refund Stars.

---

## Текущее состояние (что уже хорошо)

| Область | Статус |
|---------|--------|
| Модель «бесплатно + добровольно» | ✅ |
| Payload + pre_checkout + idempotent charge | ✅ |
| Presets, своя сумма, история донатов | ✅ |
| `/thanks`, «Ещё», `/status`, admin stats | ✅ |
| Nudge с «Не сейчас», только личка | ✅ (с оговорками ниже) |

---

## Проблемы (из аудита)

| # | Проблема | Impact | Effort |
|---|----------|--------|--------|
| P0.1 | Режим «своя сумма» перехватывает фразы напоминаний | 🔴 core UX | S |
| P0.2 | Invoice может уйти в групповой чат (`chat_id` ≠ личка) | 🔴 платёж | S |
| P1.1 | Nudge: cooldown ставится **до** успешной отправки | 🟠 надёжность | XS |
| P1.2 | Текст `/thanks` дублирует inline-кнопки | 🟡 шум | XS |
| P1.3 | Invoice description «лимит 1–2500» — тех. шум | 🟡 UX | XS |
| P2.1 | Nudge после каждого «Готово» — может утомлять | 🟡 продукт | S |
| P2.2 | `/subscribe` всё ещё упоминает Pro новым пользователям | 🟡 копирайт | S |
| P2.3 | Cooldown nudge in-memory — сброс при рестарте | 🟡 ops | M |
| P3.1 | Legacy `users.is_pro` в БД | 🟢 техдолг | M |
| P3.2 | Дубликат платежа — другая клавиатура, чем success | 🟢 polish | XS |

---

## Волна M — «Prod-ready Stars» (v3.44.0)

**Релиз:** один tag после P0 + P1.  
**Оценка:** ~0.5–1 день.

### M1 — P0: не ломать напоминания (P0.1)

**Сейчас:** любой текст (кроме `/` и кнопок меню) в режиме «своя сумма» → парсер Stars.

**Сделать:**

1. Перехватывать сообщение **только если** `parse_tip_amount_input()` вернул число **или** строка «похожа на сумму» (только цифры/пробелы/⭐/stars).
2. Если в тексте есть буквы (кириллица/латиница) — **не перехватывать**: `clear_custom_amount()` опционально или оставить режим (лучше **clear + pass through** — пользователь явно ушёл в другой сценарий).
3. В `format_custom_amount_invalid` добавить подсказку: «Если хотел напоминание — просто напиши фразу; режим суммы сброшен.»

**Файлы:** `bot/handlers/tips.py`, `bot/services/stars_tips.py` (helper `looks_like_tip_amount(text)`).

**Тесты:**

- «завтра в 14 созвон» при активном waiting → **не** ответ Stars, режим сброшен.
- «75 ⭐» → invoice как сейчас.
- «abc» → ошибка, режим **остаётся** (явно неверная сумма).

**DoD:** create-handler получает фразу с буквами; 3+ теста green.

---

### M2 — P0: invoice всегда в личку (P0.2)

**Сейчас:** presets → `chat_id=user_id` ✅; своя сумма → `message.chat.id` ❌ в группах.

**Сделать:**

1. `send_tip_invoice` всегда с `chat_id=user_id` (личка).
2. Если `message.chat.id != user_id` — в текущий чат: «💫 Счёт на N ⭐ отправлен в личку».
3. То же для `cb_tip_pay` из inline в группе (если callback пришёл из группы).

**Файлы:** `bot/services/stars_tips.py`, `bot/handlers/tips.py`, `bot/handlers/payments.py`.

**Тесты:** mock group chat (`chat_id != user_id`) → `send_invoice` вызван с `user_id`.

**DoD:** ни один invoice не уходит в group/supergroup chat_id.

---

### M3 — P1: надёжность и копирайт (P1.1–P1.3)

| Задача | Изменение |
|--------|-----------|
| M3.1 Nudge cooldown | `mark_tip_nudge_sent` **после** успешного `send_message` |
| M3.2 `/thanks` текст | Убрать перечисление presets из текста; оставить «выбери кнопку или свою сумму» |
| M3.3 Invoice desc | «Добровольная поддержка · N ⭐» без «лимит …» |
| M3.4 Duplicate pay | `tip_thank_you_keyboard()` и на duplicate path |

**DoD:** правки в `callbacks.py`, `stars_tips.py`, `payments.py`; тест nudge mark on failure.

---

### M4 — Ops smoke (ручное, Wispbyte)

После деплoy v3.44.0 + `STARS_TIPS_ENABLED=true`:

- [ ] `/ping` → v3.44.0+
- [ ] `/thanks` в **личке** → preset → оплата (test Stars)
- [ ] `/thanks` в **группе** (если доступно) → счёт только в личке
- [ ] «Другая сумма» → ввод «завтра созвон» → создаётся напомinание, не ошибка Stars
- [ ] «✅ Готово» → nudge → «Не сейчас» → повтор через 14 дней не раньше
- [ ] Admin panel → Stars summary
- [ ] `alembic upgrade head` (без новых миграций в M)

---

## Волна M2 — «Мягче и умнее» (v3.44.x, опционально)

**Когда:** после первых реальных донатов или feedback.

### M2.1 — Nudge 2.0 (P2.1)

Env-варианты (один или комбо):

```env
STARS_TIP_NUDGE_MIN_DONES=3      # nudge после N закрытых напоминаний
STARS_TIP_NUDGE_ONCE=true        # только один раз ever (БД)
```

**Хранение:** поле `users.tip_nudge_sent_at` или reuse `star_payments` + counter done events — без over-engineering предпочтительно одна колонка на `users`.

### M2.2 — `/subscribe` без Pro (P2.2)

- Новым пользователям (`onboarding_done` и never `is_pro`) — сразу `/thanks` без упоминания Pro.
- Старым — короткий redirect ещё 1–2 релиза, потом удалить.

### M2.3 — Cooldown nudge в БД (P2.3)

- Колонка `users.tip_nudge_at` · миграция `202606xx_0005`.
- In-memory fallback убрать.

---

## Волна M3 — Техдолг (backlog)

| # | Задача | Примечание |
|---|--------|------------|
| M3.1 | Удалить использование `is_pro` / документировать drop column | Отдельная миграция, не срочно |
| M3.2 | Admin: топ донатеров за 7/30 дней | Nice-to-have |
| M3.3 | `scripts/smoke_stars.py` | По аналогии с `smoke_nlp.py` |

---

## Что не делать

- ❌ Лимиты напоминаний / Pro-подписка
- ❌ Nudge в группах
- ❌ Обязательный донат перед функциями
- ❌ Публичный «рейтинг донатеров» без явного согласия

---

## Definition of Done — волна M (v3.44.0)

- [ ] P0.1 + P0.2 + P1.1–P1.3 в коде
- [ ] +8…12 тестов (group invoice, phrase passthrough, nudge mark)
- [ ] `docs/guides/stars-tips.md` + CHANGELOG + release note
- [ ] CI green, doc metrics (версия, счёт тестов)
- [ ] Ops smoke M4 пройден на Wispbyte

---

## Порядок работ (для агента / разработчика)

```
M1 (passthrough) → M2 (invoice DM) → M3 (polish) → тесты → docs → v3.44.0
         ↓
    ops smoke M4
         ↓
    M2 волна по feedback (отложено)
```

**Следующий шаг:** реализовать M1 + M2 (P0) — минимальный блокер перед `STARS_TIPS_ENABLED=true` на проде.
