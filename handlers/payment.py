import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS

logger = logging.getLogger(__name__)
from database import Database
from keyboards.admin_kb import payment_action_kb
from keyboards.user_kb import main_menu_kb, payment_kb

router = Router()


class PaymentSG(StatesGroup):
    waiting_screenshot = State()


# ── Step 1: show card details ─────────────────────────────────────────────────

@router.callback_query(F.data == "pay_start")
async def callback_pay_start(callback: CallbackQuery, db: Database):
    price = await db.get_setting("price")
    card_number = await db.get_setting("card_number")
    card_owner = await db.get_setting("card_owner")
    await callback.message.edit_text(
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"💰 Narx: <b>{int(price):,} so'm</b>\n"
        f"💳 Karta raqami: <code>{card_number}</code>\n"
        f"👤 Karta egasi: <b>{card_owner}</b>\n\n"
        "To'lovni amalga oshirib, <b>✅ To'lov qildim</b> tugmasini bosing.",
        reply_markup=payment_kb(),
    )
    await callback.answer()


# ── Step 2: ask for screenshot ────────────────────────────────────────────────

@router.callback_query(F.data == "payment_done")
async def callback_payment_done(callback: CallbackQuery, state: FSMContext, db: Database):
    user = callback.from_user

    if await db.is_paid(user.id):
        await callback.answer("✅ Siz allaqachon to'lov qilgansiz!", show_alert=True)
        await callback.message.answer(
            "✅ Botdan foydalanishingiz mumkin.", reply_markup=main_menu_kb()
        )
        return

    await state.set_state(PaymentSG.waiting_screenshot)
    await callback.message.answer(
        "📸 Iltimos, to'lov chekini (screenshot) yuboring:"
    )
    await callback.answer()


# ── Step 3: receive screenshot and forward to payment group ───────────────────

@router.message(PaymentSG.waiting_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext, db: Database):
    user = message.from_user

    if await db.is_paid(user.id):
        await state.clear()
        await message.answer(
            "✅ Siz allaqachon to'lov qilgansiz!", reply_markup=main_menu_kb()
        )
        return

    photo = message.photo[-1]
    request_id = await db.add_payment_request(user.id)
    await db.set_screenshot(request_id, photo.file_id)
    await state.clear()

    await message.answer(
        "✅ To'lov cheki qabul qilindi! Admin tasdiqlaguncha kuting."
    )

    # Forward screenshot to payment group (or admins if group not set)
    payment_group_id = await db.get_setting("payment_group_id")
    username_str = f"@{user.username}" if user.username else "—"
    caption = (
        f"💳 <b>Yangi to'lov so'rovi</b>\n\n"
        f"👤 Ism: <b>{user.full_name}</b>\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📱 Username: {username_str}"
    )

    targets: list[int] = (
        [int(payment_group_id)] if payment_group_id else list(ADMIN_IDS)
    )
    sent = False
    for target in targets:
        try:
            await message.bot.send_photo(
                target,
                photo=photo.file_id,
                caption=caption,
                reply_markup=payment_action_kb(request_id, user.id),
            )
            sent = True
        except Exception as e:
            logger.error("To'lov guruhiga yuborishda xato (chat_id=%s): %s", target, e)
            # Notify admins about the delivery failure
            for admin_id in ADMIN_IDS:
                try:
                    await message.bot.send_message(
                        admin_id,
                        f"⚠️ To'lov guruhi IDsi noto'g'ri yoki bot guruhda admin emas!\n"
                        f"🆔 Guruh ID: <code>{target}</code>\n"
                        f"❗ Xato: {e}\n\n"
                        "Iltimos, to'g'ri ID kiriting (manfiy son, masalan: <code>-1002938796047</code>)",
                    )
                except Exception:
                    pass


@router.message(PaymentSG.waiting_screenshot)
async def screenshot_wrong_type(message: Message):
    await message.answer("❌ Iltimos, screenshot (rasm) yuboring!")


# ── Approve ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("approve:"))
async def callback_approve(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    _, req_id_str, user_id_str = callback.data.split(":")
    request_id, user_id = int(req_id_str), int(user_id_str)

    await db.update_payment_status(request_id, "approved")
    await db.set_paid(user_id)

    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ <b>TASDIQLANDI</b>"
    )
    await callback.answer("✅ To'lov tasdiqlandi!")

    try:
        await callback.bot.send_message(
            user_id,
            "✅ To'lovingiz tasdiqlandi! Endi botdan foydalanishingiz mumkin.",
            reply_markup=main_menu_kb(),
        )
    except Exception:
        pass


# ── Reject ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("reject:"))
async def callback_reject(callback: CallbackQuery, db: Database):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    _, req_id_str, user_id_str = callback.data.split(":")
    request_id, user_id = int(req_id_str), int(user_id_str)

    await db.update_payment_status(request_id, "rejected")

    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ <b>RAD ETILDI</b>"
    )
    await callback.answer("❌ To'lov rad etildi!")

    try:
        await callback.bot.send_message(
            user_id,
            "❌ To'lovingiz rad etildi. Qayta to'lov qiling yoki admin bilan bog'laning.",
        )
    except Exception:
        pass
