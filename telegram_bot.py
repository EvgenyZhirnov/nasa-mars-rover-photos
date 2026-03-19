"""
Telegram bot: sends Mars Rover animations via Telegram.
Uses config for all paths. Gracefully skips when token is absent.
"""
import logging
import asyncio
from datetime import datetime

import config

logger = logging.getLogger(__name__)


async def _send_animation_async(chat_id: str) -> bool:
    """Internal async implementation for sending the animation."""
    import telegram

    anim_path = config.ANIMATION_MP4 if config.ANIMATION_MP4.exists() else (
        config.ANIMATION_GIF if config.ANIMATION_GIF.exists() else None
    )

    if anim_path is None:
        logger.error("No animation file found to send")
        return False

    try:
        bot = telegram.Bot(token=config.TELEGRAM_BOT_TOKEN)
        caption = f"Mars Rover Daily Animation — {datetime.now().strftime('%Y-%m-%d')}"

        with open(anim_path, 'rb') as f:
            if anim_path.suffix == '.mp4':
                await bot.send_video(chat_id=chat_id, video=f,
                                     caption=caption, supports_streaming=True)
            else:
                await bot.send_animation(chat_id=chat_id, animation=f, caption=caption)

        logger.info(f"Animation sent to chat {chat_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to send animation: {e}")
        return False


def send_animation(chat_id: str | None = None) -> bool:
    """Synchronous wrapper used by the scheduler."""
    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping send")
        return False

    target = chat_id or config.TELEGRAM_CHAT_ID
    if not target:
        logger.warning("No chat ID available — skipping send")
        return False

    return asyncio.run(_send_animation_async(target))


class TelegramBot:
    """
    Thin wrapper used by bootstrap.
    Command handling is not implemented (requires separate async setup for PTB v22+).
    Animation delivery is handled via the standalone send_animation() function.
    """

    def __init__(self):
        self._active = bool(config.TELEGRAM_BOT_TOKEN)
        if not self._active:
            logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram integration disabled")

    def start(self):
        if self._active:
            logger.info("Telegram bot ready (animation sending enabled via scheduler)")

    def stop(self):
        pass
