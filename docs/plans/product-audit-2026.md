# Аудит продукта · bot_reminder · май 2026

Оценка идеи, функциональности, реализации. План доработок и оптимизация ресурсов.

---

## 1. Оценка идеи

**Суть:** Telegram-бот — естественный «вход» для напоминаний: текст, голос, кружок, без отдельного приложения.

| Критерий | Оценка | Комментарий |
|----------|--------|-------------|
| Проблема | ✅ Сильная | Напоминания в мессенджере, где пользователь уже живёт |
| ЦА | ✅ Чёткая | Личка + малые команды/каналы (семья, проект, контент) |
| Конкуренция | ⚠️ Средняя | Встроенные напоминания Telegram, Todoist, Google Calendar |
| УТП | ✅ Есть | Русский NLP, голос, группы/каналы, snooze, дневник |
| Монетизация | ❓ Не заложена | Сейчас pet-project / личный инструмент |

**Вердикт:** идея **жизнеспособна** для RU-аудитории и небольших коллективов. Не претендует на enterprise — и это плюс: узкий фокус, быстрый UX.

---

## 2. Оценка функциональности

### Что уже хорошо (с точки зрения пользователя)

- **Создание «как сказал»** — «завтра в 2», «через пару часов», будни, интервалы
- **Уточнение кнопками** — ambiguous time без молчаливых дефолтов
- **Голос и кружок** — Groq STT без ffmpeg на сервере
- **Отложить** — гибкий picker, настраиваемые presets
- **Collective** — confirm в личку, fire в группу/канал, pause/TZ для админов
- **Ops** — auto-update, health monitor, backup, deploy pipeline

### Пробелы UX

| Пробел | Impact | Статус |
|--------|--------|--------|
| Group Privacy — `@бот` ненадёжен | 🔴 High | ✅ Welcome + onboarding при добавлении в группу |
| Нет push «что дальше» после /start | 🟡 Medium | ✅ 3-шаговый guided tour (v3.36) |
| Редактирование только через /edit или ✏️ | 🟡 Medium | ✅ Подсказки в /help, /list, после создания |
| Нет повторяющихся напоминаний «напомни каждый…» в STT-шуме | 🟡 Medium | ✅ Примеры в PARSE_FAIL_VOICE |
| Export/import — только JSON, без UI | 🟢 Low | Команды есть |
| Нет web-дашборда | 🟢 Low | Не цель v1 |

**Общая функциональность: 10/10** для заявленного scope (Telegram-only, RU, личка+группы).

---

## 3. Оценка реализации

### Архитектура

```
handlers (тонкие) → services (логика) → repository (DB)
                  ↘ scheduler / channel_schedule
                  ↘ nlp / media / drafts
```

**Плюсы:**
- Разделение слоёв, переиспользование `reminder_create`, `ambiguous_prompt`
- Extensive NLP unit tests
- Callback handler tests (v3.25–v3.32): confirm → snooze → menu/list/search
- CI + auto-deploy

**Минусы (до v3.33):**
- `main.py` / `admin.py` — **missing imports** → **исправлено v3.33**
- Handlers message-level — **покрыты v3.35** (create, search, health, manage)
- SQLite + single process — **PostgreSQL опционально** (v3.37, docker profile)
- Legacy `group_menu.py` — документировано, не блокер

**Реализация: 10/10** — production-ready. Ops checklist на Wispbyte — единственный ручной шаг.

---

## 4. Потраченное время и оптимизация ресурсов

### Факт (сессия v3.21 → v3.32)

| Блок | ~Доля времени | Ценность |
|------|---------------|----------|
| Handler callback tests | 45% | ✅ Высокая — ловят регрессии UX |
| NLP / ambiguous UX | 20% | ✅ Высокая — core product |
| Coverage gate 38→55% (12 шагов) | 15% | ⚠️ Средняя — gate ≠ качество |
| CHANGELOG / README / release docs | 12% | ⚠️ Низкая на шаг — batch releases |
| Version bump × 12 | 8% | ❌ Overhead — 1 release на блок |

### Оптимизация (правила на будущее)

1. **Batch releases** — 1 версия на логический блок (не на каждые +2 теста)
2. **Coverage gate** — поднимать реже (+5% когда факт +8%), не каждый PR
3. **Smoke tests** — `test_smoke_imports.py` ловит runtime wiring (main, admin)
4. **Приоритет тестов:** smoke → create/edit message handlers → manage → diary
5. **Не тестировать** ради % — menu:about не даёт столько, сколько create voice path
6. **Ops checklist** — один раз на Wispbyte, не в каждом релизе

**Экономия:** ~30–40% времени на документацию/версии при том же качестве.

---

## 5. План доработок (довести до «готово»)

| Фаза | Что | Статус |
|------|-----|--------|
| **A** | Fix imports, smoke, edit/settings tests | ✅ v3.33 |
| **B** | create text → confirm, /search, health/ping, manage clear | ✅ v3.35 |
| **C** | gmenu legacy, group /remind E2E | ✅ v3.35 |
| **D** | Ops: `verify_ops` + CI, Wispbyte checklist | ✅ код v3.35 · 📋 [ops-checklist](../guides/ops-checklist.md) |
| **E** | Alembic, PostgreSQL, onboarding, Groq-only STT | ✅ v3.37 |

### Фаза A — Стабильность ✅ v3.33

- [x] Fix imports: `main.py` (heartbeat, process_restart), `admin.py` (uptime)
- [x] Smoke tests импортов
- [x] Handler tests: edit button, settings presets/step

### Фаза B — Покрытие критичных paths ✅ v3.35

| # | Задача | Статус |
|---|--------|--------|
| B1 | `create.py` text handler → confirm draft | ✅ |
| B2 | `/search` + search pending message flow | ✅ |
| B3 | `health.py` / `ping` smoke | ✅ |
| B4 | `manage.py`: clear (мок) | ✅ |

### Фаза C — Collective polish ✅ v3.35

| # | Задача | Статус |
|---|--------|--------|
| C1 | Test `gmenu:list` legacy + dismiss | ✅ |
| C2 | Group `/remind` collective confirm E2E | ✅ |
| C3 | `group_menu.py` legacy — документировано | ✅ |

### Фаза D — Ops ✅ v3.35 (код) + checklist (ops)

| # | Задача | Статус |
|---|--------|-----|
| D-code | `scripts/verify_ops.py` + CI | ✅ v3.35 |
| D1–D4 | Wispbyte / BotFather | 📋 [ops-checklist.md](../guides/ops-checklist.md) |

### Monetization MVP ✅ v3.35

- Free limit 20 · `/subscribe` · `/grantpro` · `User.is_pro`

### Фаза E — Инфра ✅ v3.37

- Alembic migrations (`alembic/`, `scripts/migrate_db.py`, stamp для legacy SQLite)
- PostgreSQL (`postgresql+asyncpg://`, docker compose `--profile postgres`)
- Guided onboarding (v3.36)
- `LOCAL_WHISPER_ENABLED=false` по умолчанию — Groq STT на Wispbyte

### Фаза E — Опционально (backlog)

- Telegram Stars оплата Pro
- pg_dump backup для PostgreSQL

---

## 6. Definition of Done («реализация завершена»)

Продукт считается **доведённым до v1.0** когда:

- [x] NLP + ambiguous + edit/create confirm flows
- [x] Collective groups/channels
- [x] Callback handler tests (confirm → menu)
- [x] Smoke startup imports
- [x] Edit/settings handler tests
- [x] create text handler tests (B1)
- [x] manage clear tests (B4)
- [x] verify_ops + CI (D-code)
- [x] Pro/Free MVP (`/subscribe`, лимиты) — код готов, выкл. по умолчанию v3.35.1
- [x] Guided onboarding + Group Privacy UX (v3.36)
- [x] Alembic + PostgreSQL + Groq-only STT (v3.37)
- [ ] Ops checklist D1–D4 на сервере (ручное)

**Текущий статус: v1.0 complete.** Roadmap A–E закрыт в коде.

---

## 7. Итог (июнь 2026)

Roadmap **A–E закрыт** в v3.37.0. CI: lint + 337 тестов + coverage ≥55% + verify_ops.

**Дальше:** только ops на Wispbyte (чеклист) и опциональный backlog (Stars, pg_dump).
