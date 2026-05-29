from datetime import datetime, timezone

_started_at = datetime.now(timezone.utc)


def uptime_seconds() -> int:
    return int((datetime.now(timezone.utc) - _started_at).total_seconds())


def format_uptime(secs: int) -> str:
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}ч {m}м"
    if m:
        return f"{m}м {s}с"
    return f"{s}с"
