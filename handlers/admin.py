from aiogram import Router, F
from aiogram.filters import Command, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import ADMIN_IDS
from database import Database
from keyboards.admin_kb import admin_panel_kb, back_kb, payment_action_kb

router = Router()


# ── Admin filter ──────────────────────────────────────────────────────────────

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


# ── FSM States ────────────────────────────────────────────────────────────────

class AdminSG(StatesGroup):
    set_price = State()
    set_card_number = State()
    set_card_owner = State()
    set_channel_id = State()
    set_channel_link = State()
    set_random_min = State()
    set_random_max = State()
    broadcast = State()
    set_payment_group_id = State()
    set_welcome_text = State()


# ── Helpers ───────────────────────────────────────────────────────────────────

BACK = "🔙 Orqaga"


async def go_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔧 Admin paneli", reply_markup=admin_panel_kb())


# ── Entry points ──────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    await state.clear()
    await message.answer("👨‍💼 <b>Admin paneli</b>", reply_markup=admin_panel_kb())


@router.message(F.text == "📊 Statistika", IsAdmin())
async def stats(message: Message, db: Database):
    total, paid, pending = await db.get_stats()
    price = await db.get_setting("price")
    card = await db.get_setting("card_number")
    channel_id = await db.get_setting("channel_id")
    rmin = await db.get_setting("random_min")
    rmax = await db.get_setting("random_max")
    group_id = await db.get_setting("payment_group_id")

    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"✅ To'lov qilganlar: <b>{paid}</b>\n"
        f"⏳ Kutayotgan to'lovlar: <b>{pending}</b>\n\n"
        f"💰 Joriy narx: <b>{int(price):,} so'm</b>\n"
        f"💳 Karta: <code>{card}</code>\n"
        f"📢 Kanal: <b>{channel_id or 'belgilanmagan'}</b>\n"
        f"💬 To'lov guruhi: <b>{group_id or 'belgilanmagan'}</b>\n"
        f"🎲 Random: {rmin} – {rmax}",
        reply_markup=admin_panel_kb(),
    )


# ── Set price ─────────────────────────────────────────────────────────────────

@router.message(F.text == "💰 Narx belgilash", IsAdmin())
async def ask_price(message: Message, state: FSMContext):
    await state.set_state(AdminSG.set_price)
    await message.answer("💰 Yangi narxni kiriting (so'mda):", reply_markup=back_kb())


@router.message(AdminSG.set_price, IsAdmin())
async def save_price(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    raw = message.text.replace(" ", "").replace(",", "").replace(".", "")
    if not raw.isdigit():
        await message.answer("❌ Iltimos, faqat raqam kiriting!")
        return
    await db.set_setting("price", raw)
    await state.clear()
    await message.answer(
        f"✅ Narx <b>{int(raw):,} so'm</b> ga o'zgartirildi!",
        reply_markup=admin_panel_kb(),
    )


# ── Set card number ───────────────────────────────────────────────────────────

@router.message(F.text == "💳 Karta ma'lumotlari", IsAdmin())
async def ask_card_number(message: Message, state: FSMContext):
    await state.set_state(AdminSG.set_card_number)
    await message.answer("💳 Karta raqamini kiriting:", reply_markup=back_kb())


@router.message(AdminSG.set_card_number, IsAdmin())
async def save_card_number(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    await db.set_setting("card_number", message.text.strip())
    await state.set_state(AdminSG.set_card_owner)
    await message.answer("👤 Karta egasining ismini kiriting:")


@router.message(AdminSG.set_card_owner, IsAdmin())
async def save_card_owner(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    await db.set_setting("card_owner", message.text.strip())
    card = await db.get_setting("card_number")
    await state.clear()
    await message.answer(
        f"✅ Karta ma'lumotlari saqlandi!\n"
        f"💳 Raqam: <code>{card}</code>\n"
        f"👤 Egasi: <b>{message.text.strip()}</b>",
        reply_markup=admin_panel_kb(),
    )


# ── Set mandatory channel ─────────────────────────────────────────────────────

@router.message(F.text == "📢 Kanal belgilash", IsAdmin())
async def ask_channel_id(message: Message, state: FSMContext):
    await state.set_state(AdminSG.set_channel_id)
    await message.answer(
        "📢 Kanal username yoki ID sini kiriting.\n"
        "Misol: <code>@mening_kanalim</code> yoki <code>-1001234567890</code>\n\n"
        "<i>Bot kanalda admin bo'lishi shart!</i>",
        reply_markup=back_kb(),
    )


@router.message(AdminSG.set_channel_id, IsAdmin())
async def save_channel_id(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    channel_id = message.text.strip()
    await db.set_setting("channel_id", channel_id)
    await state.set_state(AdminSG.set_channel_link)
    await message.answer(
        "🔗 Kanal invite linkini kiriting (foydalanuvchilarga ko'rsatiladi):\n"
        "Misol: <code>https://t.me/mening_kanalim</code>\n\n"
        "Yoki '⏩ O'tkazib yuborish' yozing — link avtomatik hosil bo'ladi."
    )


@router.message(AdminSG.set_channel_link, IsAdmin())
async def save_channel_link(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    channel_id = await db.get_setting("channel_id")
    if message.text.strip().lower() in ("⏩ o'tkazib yuborish", "skip"):
        link = f"https://t.me/{channel_id.lstrip('@')}"
    else:
        link = message.text.strip()
    await db.set_setting("channel_link", link)
    await state.clear()
    await message.answer(
        f"✅ Kanal belgilandi!\n"
        f"🆔 ID: <code>{channel_id}</code>\n"
        f"🔗 Link: {link}",
        reply_markup=admin_panel_kb(),
    )


# ── Set random range ──────────────────────────────────────────────────────────

@router.message(F.text == "🎲 Random diapazon", IsAdmin())
async def ask_random_min(message: Message, state: FSMContext):
    await state.set_state(AdminSG.set_random_min)
    await message.answer("🎲 Minimum raqamni kiriting:", reply_markup=back_kb())


@router.message(AdminSG.set_random_min, IsAdmin())
async def save_random_min(message: Message, state: FSMContext):
    if message.text == BACK:
        await go_back(message, state)
        return
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Iltimos, faqat butun son kiriting!")
        return
    await state.update_data(random_min=int(message.text.strip()))
    await state.set_state(AdminSG.set_random_max)
    await message.answer("🎲 Maximum raqamni kiriting:")


@router.message(AdminSG.set_random_max, IsAdmin())
async def save_random_max(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Iltimos, faqat butun son kiriting!")
        return
    rmax = int(message.text.strip())
    data = await state.get_data()
    rmin = data.get("random_min", 1)
    if rmax <= rmin:
        await message.answer(
            f"❌ Maximum ({rmax}) minimum ({rmin}) dan katta bo'lishi kerak!"
        )
        return
    await db.set_setting("random_min", str(rmin))
    await db.set_setting("random_max", str(rmax))
    await state.clear()
    await message.answer(
        f"✅ Random diapazon o'zgartirildi: <b>{rmin} – {rmax}</b>",
        reply_markup=admin_panel_kb(),
    )


# ── Pending payments ──────────────────────────────────────────────────────────

@router.message(F.text == "📋 Kutayotgan to'lovlar", IsAdmin())
async def pending_payments(message: Message, db: Database):
    requests = await db.get_pending_requests()
    if not requests:
        await message.answer("📋 Hozircha kutayotgan to'lovlar yo'q.", reply_markup=admin_panel_kb())
        return
    for req_id, user_id, username, full_name, created_at in requests:
        uname = f"@{username}" if username else "—"
        await message.answer(
            f"💳 <b>To'lov so'rovi #{req_id}</b>\n\n"
            f"👤 Ism: <b>{full_name}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📱 Username: {uname}\n"
            f"📅 Sana: {created_at}",
            reply_markup=payment_action_kb(req_id, user_id),
        )


# ── Set payment group ─────────────────────────────────────────────────────────

@router.message(F.text == "💬 To'lov guruhi", IsAdmin())
async def ask_payment_group(message: Message, state: FSMContext):
    await state.set_state(AdminSG.set_payment_group_id)
    await message.answer(
        "💬 To'lov guruhi ID sini kiriting.\n"
        "Misol: <code>-1001234567890</code>\n\n"
        "<i>Bot guruhda admin bo'lishi shart!</i>\n"
        "Guruhni topish: guruhda /start yuboring yoki bot @userinfobot orqali ID oling.",
        reply_markup=back_kb(),
    )


@router.message(AdminSG.set_payment_group_id, IsAdmin())
async def save_payment_group(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    raw = message.text.strip()
    try:
        gid = int(raw)
    except ValueError:
        await message.answer(
            "❌ ID raqam bo'lishi kerak!\n"
            "Misol: <code>-1002938796047</code>\n\n"
            "<i>Guruh IDsi har doim manfiy son bo'ladi!</i>"
        )
        return
    if gid > 0:
        await message.answer(
            "❌ Guruh IDsi manfiy son bo'lishi kerak!\n"
            f"Siz kiritgansiz: <code>{raw}</code>\n\n"
            "To'g'ri format: <code>-1002938796047</code>\n"
            "(<code>-100</code> prefiksini qo'shing va qayta kiriting)"
        )
        return
    await db.set_setting("payment_group_id", raw)
    await state.clear()
    await message.answer(
        f"✅ To'lov guruhi belgilandi!\n🆔 ID: <code>{raw}</code>",
        reply_markup=admin_panel_kb(),
    )


# ── Set welcome text ──────────────────────────────────────────────────────────

@router.message(F.text == "📝 Xush kelish matni", IsAdmin())
async def ask_welcome_text(message: Message, state: FSMContext):
    await state.set_state(AdminSG.set_welcome_text)
    await message.answer(
        "📝 Foydalanuvchilarga ko'rsatiladigan xush kelish matnini kiriting:\n\n"
        "<i>HTML formatlash qo'llab-quvvatlanadi: &lt;b&gt;qalin&lt;/b&gt;, "
        "&lt;i&gt;kursiv&lt;/i&gt;, &lt;code&gt;kod&lt;/code&gt;</i>",
        reply_markup=back_kb(),
    )


@router.message(AdminSG.set_welcome_text, IsAdmin())
async def save_welcome_text(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return
    await db.set_setting("welcome_text", message.text.strip())
    await state.clear()
    await message.answer(
        "✅ Xush kelish matni saqlandi!",
        reply_markup=admin_panel_kb(),
    )


# ── Broadcast ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📨 Hammaga xabar", IsAdmin())
async def ask_broadcast(message: Message, state: FSMContext):
    await state.set_state(AdminSG.broadcast)
    await message.answer(
        "📨 Barcha foydalanuvchilarga yuboriladigan xabarni yozing.\n"
        "(Matn, rasm, video — qabul qilinadi)",
        reply_markup=back_kb(),
    )


@router.message(AdminSG.broadcast, IsAdmin())
async def do_broadcast(message: Message, state: FSMContext, db: Database):
    if message.text == BACK:
        await go_back(message, state)
        return

    await state.clear()
    user_ids = await db.get_all_user_ids()
    total = len(user_ids)
    success = failed = 0

    status_msg = await message.answer(f"📨 Yuborilmoqda… 0 / {total}")

    for i, uid in enumerate(user_ids, start=1):
        try:
            await message.copy_to(uid)
            success += 1
        except Exception:
            failed += 1
        if i % 20 == 0:
            try:
                await status_msg.edit_text(f"📨 Yuborilmoqda… {i} / {total}")
            except Exception:
                pass

    await status_msg.edit_text(
        f"✅ Xabar yuborish yakunlandi!\n\n"
        f"✅ Muvaffaqiyatli: <b>{success}</b>\n"
        f"❌ Xato: <b>{failed}</b>"
    )
    await message.answer("🔧 Admin paneli", reply_markup=admin_panel_kb())
