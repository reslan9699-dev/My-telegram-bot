"""Application configuration loaded from environment variables (.env).

Every value is read once at startup and exposed through a frozen dataclass.
Missing optional values fall back to sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _parse_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings for the bot."""

    bot_token: str
    admin_id: int
    channel_id: str
    database_url: str
    log_level: str
    rate_limit_max: int
    rate_limit_window: int
    progress_update_interval: int

    @property
    def has_bot_token(self) -> bool:
        return bool(self.bot_token)


@lru_cache
def get_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        admin_id=_parse_int("ADMIN_ID", 0),
        channel_id=os.getenv("CHANNEL_ID", "").strip(),
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        rate_limit_max=_parse_int("RATE_LIMIT_MAX", 20),
        rate_limit_window=_parse_int("RATE_LIMIT_WINDOW", 30),
        progress_update_interval=_parse_int("PROGRESS_UPDATE_INTERVAL", 3),
    )


settings = get_settings()
