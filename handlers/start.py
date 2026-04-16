from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS
from database import Database
from keyboards.admin_kb import admin_panel_kb
from keyboards.user_kb import subscribe_kb, pay_start_kb, main_menu_kb
from utils.helpers import is_subscribed

router = Router()

_DEFAULT_WELCOME = (
    "👋 <b>Botga xush kelibsiz!</b>\n\n"
    "Botdan foydalanish uchun to'lovni amalga oshiring."
)


async def _send_welcome(target: Message, db: Database):
    welcome_text = await db.get_setting("welcome_text")
    if not welcome_text:
        welcome_text = _DEFAULT_WELCOME
    await target.answer(welcome_text, reply_markup=pay_start_kb())


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    user = message.from_user
    await db.add_user(user.id, user.username or "", user.full_name)

    # Admin → show admin panel
    if user.id in ADMIN_IDS:
        await message.answer(
            "👨‍💼 <b>Admin paneliga xush kelibsiz!</b>",
            reply_markup=admin_panel_kb(),
        )
        return

    # Check mandatory channel subscription
    channel_id = await db.get_setting("channel_id")
    channel_link = await db.get_setting("channel_link")

    if channel_id and not await is_subscribed(message.bot, user.id, channel_id):
        await message.answer(
            "📢 Botdan foydalanish uchun avval kanalga obuna bo'ling!\n\n"
            "Obuna bo'lgach, <b>✅ Obuna bo'ldim</b> tugmasini bosing.",
            reply_markup=subscribe_kb(channel_link or f"https://t.me/{channel_id.lstrip('@')}"),
        )
        return

    # Check payment
    if await db.is_paid(user.id):
        await message.answer(
            "✅ <b>Xush kelibsiz!</b>\nTugmani bosib tahminan qancha ekanligini aniqlang!",
            reply_markup=main_menu_kb(),
        )
    else:
        await _send_welcome(message, db)


@router.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: CallbackQuery, db: Database):
    user = callback.from_user
    channel_id = await db.get_setting("channel_id")
    channel_link = await db.get_setting("channel_link")

    if channel_id and not await is_subscribed(callback.bot, user.id, channel_id):
        await callback.answer("❌ Siz hali obuna bo'lmagansiz!", show_alert=True)
        return

    await callback.message.delete()

    if await db.is_paid(user.id):
        await callback.message.answer(
            "✅ <b>Xush kelibsiz!</b>", reply_markup=main_menu_kb()
        )
    else:
        await _send_welcome(callback.message, db)

    await callback.answer()
