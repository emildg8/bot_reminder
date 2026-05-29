from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field


class ParsedReminder(BaseModel):
    text: str = Field(description="Текст напоминания без времени")
    kind: Literal["once", "interval", "daily"]
    run_at: datetime | None = None
    interval_seconds: int | None = None
    daily_time: time | None = None
