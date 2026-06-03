# Автор в продукте

Как пользователь видит разработчика — без paywall и без шума в группах.

**Версия:** v3.45.8+ · см. [CHANGELOG](../../CHANGELOG.md)

## Точки входа

| Где | Что видит пользователь |
|-----|------------------------|
| После onboarding | Строка + кнопки **👤 Автор** / **🆕 v…** |
| `/author`, меню «Ещё» | Полная карточка, ссылки, правило «не в личку для срочного» |
| `/about` | Тизер + кнопки (Issue, что нового, релизы) |
| `/help` | Футер: автор, Issues, что нового, /author |
| `/status` (личка) | Строка автора и ссылка на релиз |
| После Stars | «Вопросы — /author» + кнопки **👤 Автор** / **⭐ Ещё раз** |
| `/thanks` | Добровольная поддержка (см. [stars-tips.md](stars-tips.md)) |

## Команды

- `/author` — карточка разработчика
- `/about` — о боте + тизер автора

## Константы и тексты

- `bot/texts/messages.py` — `DEVELOPER_*`, `format_developer_*`
- `bot/keyboards/inline.py` — `developer_links_keyboard`, `developer_made_by_keyboard`

## Проверка

```bash
python scripts/smoke_author.py
pytest tests/test_about.py -q
```

Telegram: onboarding → кнопки · `/status` → строка автора · `/thanks` → оплата → кнопки автора.

## Оплата

Только **Telegram Stars** (`/thanks`) — см. [stars-tips.md](stars-tips.md). Добровольная поддержка, не разблокирует функции.

Кратко для внешних описаний: бот open-source ([GitHub](https://github.com/emildg8/bot_reminder)), автор @emildg8, карточка в боте — `/author`.
