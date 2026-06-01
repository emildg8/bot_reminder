#!/usr/bin/env python3
"""CLI: применить Alembic migrations."""

from bot.db.migrate import upgrade_database


def main() -> None:
    upgrade_database()
    print("Migrations applied (head)")


if __name__ == "__main__":
    main()
