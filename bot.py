"""Protected File Distribution Bot - application entrypoint.

Run locally:      python bot.py
Run with Docker:  docker compose up --build
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from config import settings
from database.database import engine, init_db
from handlers.admin import admin_router
from handlers.callbacks import callbacks_router
from handlers.middlewares import RateLimitMiddleware
from handlers.user import user_router

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    """Assemble routers, middlewares and the global error handler."""
    dispatcher = Dispatcher(storage=MemoryStorage())

    rate_limiter = RateLimitMiddleware(settings.rate_limit_max, settings.rate_limit_window)
    user_router.message.outer_middleware(rate_limiter)
    callbacks_router.callback_query.outer_middleware(rate_limiter)

    dispatcher.include_routers(admin_router, user_router, callbacks_router)

    @dispatcher.error()
    async def global_error_handler(event: ErrorEvent) -> None:
        logger.critical("Unhandled update error", exc_info=event.exception)

    return dispatcher


async def main() -> None:
    if not settings.has_bot_token:
        raise SystemExit(
            "BOT_TOKEN is missing. Copy .env.example to .env and fill in the required values."
        )

    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = build_dispatcher()

    try:
        me = await bot.get_me()
        logger.info("Bot started as @%s (id=%s)", me.username, me.id)
        await dispatcher.start_polling(
            bot, allowed_updates=dispatcher.resolve_used_update_types()
        )
    finally:
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
