"""CLI: установка аватарки бота."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from bot.config import settings
from bot.services.bot_avatar import ensure_bot_avatar, verify_bot_has_avatar


async def run_set_and_verify(force: bool = False) -> None:
    bot = Bot(token=settings.bot_token)
    try:
        me = await bot.get_me()
        print(f"Bot: @{me.username} (id={me.id})")

        before = await verify_bot_has_avatar(bot)
        print(f"Avatar before: {'yes' if before else 'no'}")

        await ensure_bot_avatar(bot, force=force)
        print("set_my_profile_photo: OK")

        after = await verify_bot_has_avatar(bot)
        print(f"Avatar after: {'yes' if after else 'no'}")
        if not after:
            raise RuntimeError("Avatar not visible after upload")
        print("SUCCESS")
    finally:
        await bot.session.close()


def main() -> None:
    import sys

    logging.basicConfig(level=logging.INFO)
    force = "--force" in sys.argv
    asyncio.run(run_set_and_verify(force=force))


if __name__ == "__main__":
    main()
