import random

from aiogram import Router, F
from aiogram.types import Message

from config import ADMIN_IDS
from database import Database
from keyboards.user_kb import main_menu_kb, subscribe_kb, pay_start_kb
from utils.helpers import is_subscribed

router = Router()


def _weighted_value() -> float:
    """Weighted random: 70% [1-2), 20% [2-5), 7% [5-20), 2.5% [20-100), 0.5% [100-500]."""
    r = random.random()
    if r < 0.70:
        value = random.uniform(1.00, 2.00)
    elif r < 0.90:
        value = random.uniform(2.00, 5.00)
    elif r < 0.97:
        value = random.uniform(5.00, 20.00)
    elif r < 0.995:
        value = random.uniform(20.00, 100.00)
    else:
        value = random.uniform(100.00, 500.00)
    return round(value, 2)


@router.message(F.text == "🎲 Keyingisini ko'rish")
async def random_number(message: Message, db: Database):
    user = message.from_user

    # Admins bypass all checks
    if user.id in ADMIN_IDS:
        value = _weighted_value()
        await message.answer(
            f"🎲 <b>Sizning raqamingiz:</b> <code>{value}</code>x",
            reply_markup=main_menu_kb(),
        )
        return

    # Channel check
    channel_id = await db.get_setting("channel_id")
    channel_link = await db.get_setting("channel_link")
    if channel_id and not await is_subscribed(message.bot, user.id, channel_id):
        await message.answer(
            "📢 Botdan foydalanish uchun avval kanalga obuna bo'ling!",
            reply_markup=subscribe_kb(
                channel_link or f"https://t.me/{channel_id.lstrip('@')}"
            ),
        )
        return

    # Payment check
    if not await db.is_paid(user.id):
        welcome_text = await db.get_setting("welcome_text")
        if not welcome_text:
            welcome_text = (
                "👋 <b>Botga xush kelibsiz!</b>\n\n"
                "Botdan foydalanish uchun to'lovni amalga oshiring."
            )
        await message.answer(welcome_text, reply_markup=pay_start_kb())
        return

    value = _weighted_value()
    await message.answer(
        f"🎲 <b>Hozirgi Koeffisient:</b> <code>{value}</code>x",
        reply_markup=main_menu_kb(),
    )
