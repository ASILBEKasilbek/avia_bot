from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError


async def is_subscribed(bot: Bot, user_id: int, channel_id: str) -> bool:
    """Returns True if user is subscribed to the channel, or if no channel is set."""
    if not channel_id:
        return True
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status not in ("left", "kicked", "banned")
    except (TelegramBadRequest, TelegramForbiddenError):
        # Channel not found or bot is not an admin there → don't block the user
        return True
    except Exception:
        return True
