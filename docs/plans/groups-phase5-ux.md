# Фаза 5 — групповой UX (v3.16+)

Контекст: каналы и collective delivery готовы (фазы 1–4 ✅). В реальной группе («Болталка») всплыли проблемы UI и деплоя.

## Жалобы из группы (31.05)

| Проблема | Причина в коде |
|----------|----------------|
| Кнопки на ¼ экрана | `main_menu_inline_keyboard()` + `more_menu_keyboard()` + `examples_keyboard()` — как в личке |
| «Назад не работает» | `menu:more` шлёт **новое** сообщение вместо `edit_text`; у примеров нет «Назад» |
| «Ошибка» при примере | Callback в группе → confirm; возможен сбой DM / fallback |
| Шум в чате | Каждый пункт меню = отдельное сообщение |

## Принципы фазы 5

1. **Группа ≠ личка** — компактное меню, навигация через `edit_message`, без дневника/статистики в чате.
2. **Одно сообщение меню** — открыли → листаем экраны → «◀️ Меню» возвращает на главный экран.
3. **Создание** — по-прежнему `/remind@бот` или @ из списка; меню только подсказки + список + TZ.
4. **Личка** — полное меню без изменений.

---

## Блок A — Меню для групп (v3.16.0)

### A1. `group_menu_keyboard()` — компактное главное меню
```
[ 📋 Список ] [ ➕ Как создать ]
[ 🕐 TZ    ] [ ❓ Помощь     ]
```
- Callback: `gmenu:list`, `gmenu:hint`, `gmenu:tz`, `gmenu:help`
- Без «Дневник», «Статистика», «Примеры» (или одна строка «💡 Примеры» → 3 кнопки, не 8+)

### A2. Навигация edit-in-place
- Общий helper `show_group_menu(message, screen, *, edit=True)`
- Экраны: `home` | `more` | `examples` | `tz` | `help`
- Кнопка **◀️ Меню** → `gmenu:home` (edit, не новое сообщение)
- Исправить баг: `settings_snooze_keyboard` «Назад» → `menu:more` сейчас дублирует сообщение

### A3. Welcome в группе
- Заменить «⚡️ Быстрые действия» + полное меню на **одну** карточку:
  - 2 строки текста + компактная клавиатура (A1)
- Onboarding TZ — оставить отдельным сообщением (один раз)

### A4. Отключить в группах
- `menu:diary`, `menu:stats` → «📔 Дневник и статистика — в личке с ботом»
- Reply-кнопки `MENU_BUTTON_TEXTS` в группе — игнор или подсказка «используй /remind@бот»

---

## Блок B — Надёжность в группе (v3.16.1)

### B1. Примеры (`ex:`) в collective
- [x] Тест DM failure → fallback без падения
- [x] `example_picked` — try/except + текст в чат

### B2. `/list` в группе
- [x] Без edit-кнопок в collective UI; пагинация через `list:page` — тест `test_collective_list`

### B3. Ошибки
- [x] Глобальный error handler вместо «Ошибка»
- [x] Ранний callback.answer в group-меню и confirm

---

## Блок C — Тишина в чате (v3.15 частично ✅, доработать)

- [x] Короткие confirm-notice, fire в группе без дубля
- [x] Меню не плодит сообщения (A2) — v3.18: удаление старого `/menu`
- [ ] Опционально: `delete_message` старого меню через 30 с (nice-to-have)

---

## Блок D — Wispbyte / деплой

### D1. «Missing Package: bot»
**Не устанавливать.** Wispbyte путает локальный пакет `bot/` с PyPI.

| Действие | Правильно |
|----------|-----------|
| Уведомление «Missing Package bot» | **Dismiss** |
| Add to Startup | **Нет** — сломает `pip install bot` |
| Startup Command | `bash start.sh` (git pull + run) |

### D2. Startup без git pull
Текущая команда `pip install && python -m bot.main` **не обновляет код** → застревание на broken commit.

**Console (один раз):**
```bash
cd /home/container && git pull origin main && bash start.sh
```

**Постоянно:** Startup Command = `bash start.sh`

### D3. Crash loop
- v3.15.2+ — без `os.execv`, exit 0 для restart
- Stale `data/bot.lock` — автоочистка ✅

---

## Матрица после фазы 5

| Действие | Личка | Группа |
|----------|-------|--------|
| Главное меню | Reply + полное inline | Компактное inline, edit |
| Примеры | Сетка 8+ | 3–4 или только /help |
| Дневник/статистика | Да | «Открой бота в личке» |
| Назад | Работает | ◀️ Меню → edit home |
| Создать | Текст | /remind@бот |

---

## Порядок работ (оценка)

| # | Задача | Версия | Сложность |
|---|--------|--------|-----------|
| 1 | Wispbyte: startup + dismiss «bot package» | docs | 15 мин |
| 2 | `group_menu_*` + edit navigation | v3.16.0 | 2–3 ч |
| 3 | Welcome + отключить diary/stats в группе | v3.16.0 | 1 ч |
| 4 | Fix back + examples screen | v3.16.0 | 1 ч |
| 5 | Тесты collective menu + example callback | v3.16.0 | 1 ч |
| 6 | B1–B3 error UX | v3.16.1 | 1–2 ч |

---

## Критерии «групповой режим готов»

- [x] В группе нет reply-клавиатуры и нет сетки из 8+ примеров
- [x] Все submenu возвращаются кнопкой «◀️ Меню» без новых сообщений
- [x] `/remind@бот` + @ из списка + confirm в личку — ✅ assignee v3.46.4 prod (#35)
- [ ] Wispbyte на `bash start.sh`, версия в логах актуальная
- [ ] Нет ложного `pip install bot`
