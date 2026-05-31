import os

os.environ.setdefault("BOT_TOKEN", "0:test-token-for-pytest")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
