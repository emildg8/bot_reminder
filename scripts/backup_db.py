#!/usr/bin/env python3
"""CLI: backup SQLite database."""

from bot.services.backup import backup_database


def main() -> None:
    path = backup_database()
    if path:
        print(f"Backup: {path}")
    else:
        raise SystemExit("Backup failed — database not found")


if __name__ == "__main__":
    main()
