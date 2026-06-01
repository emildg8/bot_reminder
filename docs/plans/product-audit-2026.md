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
| Group Privacy — `@бот` ненадёжен | 🔴 High | Документировано, нужен onboarding |
| Нет push «что дальше» после /start | 🟡 Medium | Есть меню, но нет guided tour |
| Редактирование только через /edit или ✏️ | 🟡 Medium | Работает, но мало подсказок |
| Нет повторяющихся напоминаний «напомни каждый…» в STT-шуме | 🟡 Medium | LLM fallback помогает |
| Export/import — только JSON, без UI | 🟢 Low | Команды есть |
| Нет web-дашборда | 🟢 Low | Не цель v1 |

**Общая функциональность: 8/10** для заявленного scope (Telegram-only, RU, личка+группы).

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
- `main.py` / `admin.py` — **missing imports** (не ловились pytest) → **исправлено v3.33**
- Handlers message-level (create, manage, diary) — ~0% coverage
- SQLite + single process — нет горизонтального масштабирования
- Legacy `group_menu.py` — мёртвый gmenu, можно удалить позже
- 12 релизов за сессию тестов — overhead на changelog/version bump

**Реализация: 7.5/10** — зрелый pet-project, близок к production для личного/малый команды use case.

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

### Фаза A — Стабильность ✅ v3.33

- [x] Fix imports: `main.py` (heartbeat, process_restart), `admin.py` (uptime)
- [x] Smoke tests импортов
- [x] Handler tests: edit button, settings presets/step

### Фаза B — Покрытие критичных paths (v3.34–v3.35)

| # | Задача | Effort | Gate |
|---|--------|--------|------|
| B1 | `create.py` text handler → confirm draft | 2–3 ч | — |
| B2 | `/search` + search pending message flow | 1 ч | — |
| B3 | `health.py` / `ping` smoke | 30 мин | — |
| B4 | `manage.py`: pause/resume/clear (мок) | 2 ч | 58% |

### Фаза C — Collective polish (v3.36)

| # | Задача | Effort |
|---|--------|--------|
| C1 | Test `gmenu:list` legacy + dismiss | 1 ч |
| C2 | Group `/remind` collective confirm E2E (мок bot.send_message) | 2 ч |
| C3 | Удалить или пометить deprecated `group_menu.py` | 30 мин |

### Фаза D — Ops «готово к эксплуатации»

| # | Задача | Кто |
|---|--------|-----|
| D1 | Wispbyte Startup = `bash start.sh` | ops |
| D2 | Dismiss «Missing Package bot» | ops |
| D3 | Group Privacy off (если нужен @бот) | BotFather |
| D4 | Проверить «Бот запущен · v3.33» после deploy | ops |

### Фаза E — Опционально (backlog)

- Alembic вместо PRAGMA migrations
- PostgreSQL для multi-instance
- Guided onboarding после /start
- Удалить local Whisper default на Wispbyte (только Groq → меньше RAM)

---

## 6. Definition of Done («реализация завершена»)

Продукт считается **доведённым до v1.0** когда:

- [x] NLP + ambiguous + edit/create confirm flows
- [x] Collective groups/channels
- [x] Callback handler tests (confirm → menu)
- [x] Smoke startup imports
- [x] Edit/settings handler tests
- [ ] create text/voice handler tests (B1)
- [ ] manage pause/clear tests (B4)
- [ ] Ops checklist D1–D4 выполнен
- [ ] Coverage ≥58% на критичных modules, не на texts/help.py

**Текущий статус: ~85% до v1.0-ready.** Оставшиеся 15% — message handlers + ops, не новые фичи.

---

## 7. Рекомендация

**Не добавлять фичи** до закрытия B + D. Бот уже функционален; риск — регрессии в create/manage и ops на Wispbyte.

**Следующий коммит пользователю:** v3.33 — bugfix + smoke + edit/settings tests + этот аудит.
