from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def admin_panel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika")],
            [
                KeyboardButton(text="💰 Narx belgilash"),
                KeyboardButton(text="💳 Karta ma'lumotlari"),
            ],
            [
                KeyboardButton(text="📢 Kanal belgilash"),
                KeyboardButton(text="🎲 Random diapazon"),
            ],
            [
                KeyboardButton(text="💬 To'lov guruhi"),
                KeyboardButton(text="📝 Xush kelish matni"),
            ],
            [KeyboardButton(text="📋 Kutayotgan to'lovlar")],
            [KeyboardButton(text="📨 Hammaga xabar")],
        ],
        resize_keyboard=True,
    )


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True,
    )


def payment_action_kb(request_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"approve:{request_id}:{user_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject:{request_id}:{user_id}",
                ),
            ]
        ]
    )
