import json
import logging
from datetime import datetime, time
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI

from bot.config import settings
from bot.services.nlp.rule_parser import parse_all_with_rules, parse_with_rules
from bot.services.nlp.schemas import ParsedReminder

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты парсер напоминаний. Из текста пользователя извлеки напоминание.
Верни ТОЛЬКО JSON без markdown:
{
  "text": "текст задачи без времени",
  "kind": "once" | "interval" | "daily" | "weekly",
  "run_at": "ISO8601 datetime с timezone или null",
  "interval_seconds": число или null,
  "daily_time": "HH:MM" или null,
  "weekdays": [0..6] или null
}

Примеры:
- "через час выпить таблетки" -> once, run_at через 1 час
- "каждые 30 минут встать" -> interval, interval_seconds=1800
- "каждый день в 9:00 зарядка" -> daily, daily_time="09:00"
- "по будням в 9:00 зарядка" -> weekly, weekdays=[0,1,2,3,4], daily_time="09:00"
- "по выходным в 11:00 уборка" -> weekly, weekdays=[5,6], daily_time="11:00"
- "завтра два часа дня созвон" -> once, run_at завтра 14:00, text="созвон"
- "напомни через пару часов обед" -> once, run_at +2 часа, text="обед"
- "завтра утром зарядка" -> once, run_at завтра 09:00, text="зарядка"
Текущее время пользователя: {now}
Timezone: {timezone}
"""


def _build_client(base_url: str, api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(base_url=base_url, api_key=api_key)


def _parse_llm_json(content: str) -> ParsedReminder | None:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    daily_time = None
    if data.get("daily_time"):
        try:
            parts = str(data["daily_time"]).split(":")
            daily_time = time(int(parts[0]), int(parts[1]))
        except Exception:
            return None

    run_at = None
    if data.get("run_at"):
        try:
            run_at = datetime.fromisoformat(str(data["run_at"]).replace("Z", "+00:00"))
        except Exception:
            return None

    kind = data.get("kind")
    if kind not in ("once", "interval", "daily", "weekly"):
        return None

    interval_seconds = data.get("interval_seconds")
    if interval_seconds is not None:
        try:
            interval_seconds = int(interval_seconds)
        except Exception:
            return None

    parsed = ParsedReminder(
        text=str(data.get("text", "")).strip(),
        kind=kind,
        run_at=run_at,
        interval_seconds=interval_seconds,
        daily_time=daily_time,
        weekdays=data.get("weekdays"),
    )

    if not parsed.text:
        return None
    if parsed.kind == "once" and parsed.run_at is None:
        return None
    if parsed.kind == "interval" and (parsed.interval_seconds is None or parsed.interval_seconds <= 0):
        return None
    if parsed.kind == "daily" and parsed.daily_time is None:
        return None
    if parsed.kind == "weekly":
        if parsed.daily_time is None:
            return None
        if not parsed.weekdays or not all(isinstance(x, int) for x in parsed.weekdays):
            return None
        parsed.weekdays = [x for x in parsed.weekdays if 0 <= x <= 6]
        if not parsed.weekdays:
            return None
    return parsed


async def _try_llm(
    client: AsyncOpenAI,
    model: str,
    user_text: str,
    timezone: str,
) -> ParsedReminder | None:
    now = datetime.now(ZoneInfo(timezone)).isoformat()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT.format(now=now, timezone=timezone),
                },
                {"role": "user", "content": user_text},
            ],
            temperature=0,
            max_tokens=300,
        )
        content = response.choices[0].message.content or ""
        parsed = _parse_llm_json(content)
        if parsed and parsed.text:
            return parsed
    except Exception as exc:
        logger.warning("LLM parse failed (%s): %s", model, exc)
    return None


async def parse_all_reminders(text: str, timezone: str) -> list[ParsedReminder]:
    results = parse_all_with_rules(text, timezone)
    if results:
        logger.info("Parsed via rules (%s item(s))", len(results))
        return results

    providers: list[tuple[str, AsyncOpenAI, str]] = []

    if settings.groq_api_key:
        providers.append(
            (
                "groq",
                _build_client("https://api.groq.com/openai/v1", settings.groq_api_key),
                settings.groq_model,
            )
        )
    if settings.gemini_api_key:
        providers.append(
            (
                "gemini",
                _build_client(
                    "https://generativelanguage.googleapis.com/v1beta/openai/",
                    settings.gemini_api_key,
                ),
                settings.gemini_model,
            )
        )

    for name, client, model in providers:
        parsed = await _try_llm(client, model, text, timezone)
        if parsed:
            logger.info("Parsed via free LLM (%s)", name)
            return [parsed]

    if settings.openai_api_key:
        client = _build_client("https://api.openai.com/v1", settings.openai_api_key)
        parsed = await _try_llm(client, settings.openai_model, text, timezone)
        if parsed:
            logger.info("Parsed via OpenAI")
            return [parsed]

    return []


async def parse_reminder(text: str, timezone: str) -> ParsedReminder | None:
    items = await parse_all_reminders(text, timezone)
    return items[0] if items else None
