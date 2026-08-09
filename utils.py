"""Shared helpers: media payload extraction, HTML escaping and file sending."""

from __future__ import annotations

import html
from dataclasses import dataclass

from aiogram import Bot
from aiogram.types import Message

__all__ = [
    "FilePayload",
    "get_file_payload",
    "send_file_by_type",
    "escape_html",
    "is_supported_media",
]


@dataclass(frozen=True)
class FilePayload:
    """A Telegram file referenced only by its file_id (never downloaded)."""

    telegram_file_id: str
    file_type: str
    original_filename: str | None = None


def escape_html(text: str | None) -> str:
    """Escape a string so it is safe to send with HTML parse mode."""
    if not text:
        return ""
    return html.escape(text, quote=False)


def is_supported_media(message: Message) -> bool:
    """Return True when the message carries a media type we accept."""
    return get_file_payload(message) is not None


def get_file_payload(message: Message) -> FilePayload | None:
    """Extract a FilePayload from a message, or None if the message has no media.

    Photos use the largest available size so the download keeps full quality.
    """
    if message.document:
        return FilePayload(
            telegram_file_id=message.document.file_id,
            file_type="document",
            original_filename=message.document.file_name,
        )
    if message.photo:
        largest = message.photo[-1]
        return FilePayload(
            telegram_file_id=largest.file_id,
            file_type="photo",
            original_filename=f"photo_{largest.file_id[:12]}.jpg",
        )
    if message.video:
        return FilePayload(
            telegram_file_id=message.video.file_id,
            file_type="video",
            original_filename=message.video.file_name or f"video_{message.video.file_id[:12]}.mp4",
        )
    if message.audio:
        return FilePayload(
            telegram_file_id=message.audio.file_id,
            file_type="audio",
            original_filename=message.audio.file_name or "audio.mp3",
        )
    if message.voice:
        return FilePayload(
            telegram_file_id=message.voice.file_id,
            file_type="voice",
            original_filename="voice.ogg",
        )
    if message.video_note:
        return FilePayload(
            telegram_file_id=message.video_note.file_id,
            file_type="video_note",
            original_filename="video_note.mp4",
        )
    if message.animation:
        return FilePayload(
            telegram_file_id=message.animation.file_id,
            file_type="animation",
            original_filename=message.animation.file_name or "animation.gif",
        )
    return None


async def send_file_by_type(
    bot: Bot,
    chat_id: int | str,
    payload: FilePayload,
    caption: str | None = None,
) -> Message:
    """Forward a stored file to a chat using only its Telegram file_id.

    When resending by file_id Telegram keeps the original filename, so no
    filename argument is needed.
    """
    if payload.file_type == "document":
        return await bot.send_document(chat_id, payload.telegram_file_id, caption=caption)
    if payload.file_type == "photo":
        return await bot.send_photo(chat_id, payload.telegram_file_id, caption=caption)
    if payload.file_type == "video":
        return await bot.send_video(chat_id, payload.telegram_file_id, caption=caption)
    if payload.file_type == "audio":
        return await bot.send_audio(chat_id, payload.telegram_file_id, caption=caption)
    if payload.file_type == "voice":
        return await bot.send_voice(chat_id, payload.telegram_file_id, caption=caption)
    if payload.file_type == "video_note":
        return await bot.send_video_note(chat_id, payload.telegram_file_id)
    if payload.file_type == "animation":
        return await bot.send_animation(chat_id, payload.telegram_file_id, caption=caption)
    raise ValueError(f"Unsupported file type: {payload.file_type}")
