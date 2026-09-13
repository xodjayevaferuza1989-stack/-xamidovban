import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice

TOKEN = "8956998719:AAGvrOCmF0jx7V78E9fzriOaKZn8wRHURcg"
ADMIN_ID = 8587976365  # Siz ko'rsatgan admin ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Bazani to'liq ushlab turish uchun (test rejimida 15 ta stars bilan boshlanadi)
DATABASE = {
    "users": set(),
    "bot_balance": 15,  # Rasmda 15 stars ko'ringani uchun sinovga qo'yildi
}


class GiftStates(StatesGroup):
  waiting_for_user_id = State()
  waiting_for_custom_text = State()
  selected_gift_id = State()
  selected_gift_price = State()


GIFTS_LIST = [
    {"id": "6028601630662853006", "name": "🍾 Shampan", "price": 50},
    {"id": "5170521118301225164", "name": "💎 Brilliant", "price": 100},
    {"id": "5170690322832818290", "name": "💍 Uzuk", "price": 100},
    {"id": "5168043875654172773", "name": "🏆 Kubok", "price": 100},
    {"id": "5170564780938756245", "name": "🚀 Raketa", "price": 50},
    {"id": "5170314324215857265", "name": "💐 Guldasta", "price": 50},
    {"id": "5170144170496491616", "name": "🎂 Tort", "price": 50},
    {"id": "5168103777563050263", "name": "🌹 Atirgul", "price": 25},
    {"id": "5170250947678437525", "name": "🎁 Sovg'a qutisi", "price": 25},
    {"id": "5170233102089322756", "name": "🧸 Ayiqcha", "price": 15},
    {"id": "5170145012310081615", "name": "💝 Yurak", "price": 15},
]


@dp.message(Command("start"))
async def start_handler(message: types.Message):
  DATABASE["users"].add(message.from_user.id)

  keyboard = InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(text="⭐ Stars hadya qilish", callback_data="donate_star")]
  ])
  await message.answer(
      "Salom! Botimiz orqali loyihaga Stars hadya qilishingiz mumkin.",
      reply_markup=keyboard,
  )


@dp.callback_query(F.data == "donate_star")
async def donate_callback(callback: types.CallbackQuery, state: FSMContext):
  await callback.message.answer(
      "Nechta Stars hadya qilmoqchisiz? (Faqat raqam kiriting, masalan: 15)"
  )
  await state.set_state(GiftStates.selected_gift_price)
  await callback.answer()


@dp.message(GiftStates.selected_gift_price)
async def process_stars_amount(message: types.Message, state: FSMContext):
  if not message.text.isdigit():
    await message.answer("Iltimos, faqat butun son kiriting:")
    return

  amount = int(message.text)
  if amount < 1:
    await message.answer("Miqdor 1 dan kam bo'lmasligi kerak.")
    return

  await state.clear()
  await message.answer_invoice(
      title="Stars Hadya qilish",
      description=f"Loyihaga {amount} ta Stars hadya qilish",
      payload=f"gift_stars_{amount}",
      currency="XTR",
      prices=[LabeledPrice(label="Stars", amount=amount)],
  )


@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery):
  await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def success_payment_handler(message: types.Message):
  payment = message.successful_payment
  amount = payment.total_amount
  user = message.from_user

  DATABASE["bot_balance"] += amount

  await message.answer(
      f"Rahmat! Siz muvaffaqiyatli {amount} ta Stars hadya qildingiz! ⭐"
  )
  try:
    user_name = f"@{user.username}" if user.username else user.full_name
    await bot.send_message(
        ADMIN_ID,
        f"⭐ **Yangi Stars hadya qilindi!**\n\n"
        f"👤 Kim tomonidan: {user_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"💰 Miqdori: **{amount} ta** Stars\n"
        f"💳 Botdagi umumiy balans: **{DATABASE['bot_balance']} ta** ⭐",
        parse_mode="Markdown",
    )
  except Exception as e:
    print(f"Adminga xabar yuborishda xatolik: {e}")


# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
  if message.from_user.id != ADMIN_ID:
    await message.answer("Siz admin emassiz!")
    return

  keyboard = InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(text="🎁 Gift yechish", callback_data="admin_gifts")],
      [
          InlineKeyboardButton(
              text="📊 Statistika", callback_data="admin_stats"
          )
      ],
  ])
  await message.answer("👑 Admin panelga xush kelibsiz:", reply_markup=keyboard)


@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
  if callback.from_user.id != ADMIN_ID:
    await callback.answer("Ruxsat yo'q!", show_alert=True)
    return

  total_users = len(DATABASE["users"])
  balance = DATABASE["bot_balance"]

  text = (
      f"📊 **Bot Statistikasi:**\n\n"
      f"👥 Foydalanuvchilar soni: **{total_users} ta**\n"
      f"⭐ Jami yig'ilgan balans: **{balance} ⭐**"
  )

  await callback.message.edit_text(
      text,
      reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
          InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_admin")
      ]]),
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "admin_gifts")
async def admin_gifts_handler(callback: types.CallbackQuery):
  if callback.from_user.id != ADMIN_ID:
    await callback.answer("Ruxsat yo'q!", show_alert=True)
    return

  bot_balance = DATABASE["bot_balance"]
  text = f"💰 Sizning botdagi balansingiz: **{bot_balance} ⭐**\n\n"

  if bot_balance <= 0:
    text += "❌ Balansingizda stars mavjud emas!"
    keyboard_buttons = [[
        InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_admin")
    ]]
  else:
    can_afford_any = any(bot_balance >= gift["price"] for gift in GIFTS_LIST)
    if not can_afford_any:
      text += "❌ Balansingizdagi stars hech qanday gift narxiga yetmaydi!"
      keyboard_buttons = [[
          InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_admin")
      ]]
    else:
      text += "✅ Siz quyidagi giftlarni yuborishingiz mumkin:"
      keyboard_buttons = []
      for gift in GIFTS_LIST:
        if bot_balance >= gift["price"]:
          btn_text = f"✅ {gift['name']} ({gift['price']} ⭐)"
          cb_data = f"select_gift_{gift['id']}"
        else:
          btn_text = f"🔒 {gift['name']} ({gift['price']} ⭐) - Yetmaydi"
          cb_data = "gift_not_enough"
        keyboard_buttons.append([InlineKeyboardButton(text=btn_text, callback_data=cb_data)])
      keyboard_buttons.append([
          InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_admin")
      ])

  await callback.message.edit_text(
      text,
      reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons),
      parse_mode="Markdown",
  )


@dp.callback_query(F.data == "gift_not_enough")
async def gift_not_enough_alert(callback: types.CallbackQuery):
  await callback.answer(
      "❌ Balansingiz bu giftga yetmaydi yoki stars mavjud emas!",
      show_alert=True,
  )


@dp.callback_query(F.data.startswith("select_gift_"))
async def select_gift_handler(callback: types.CallbackQuery, state: FSMContext):
  if callback.from_user.id != ADMIN_ID:
    return

  gift_id = callback.data.split("select_gift_", 1)[1]

  selected_gift = next((g for g in GIFTS_LIST if g["id"] == gift_id), None)
  if not selected_gift:
    await callback.answer("Gift topilmadi!", show_alert=True)
    return

  if DATABASE["bot_balance"] < selected_gift["price"]:
    await callback.answer("Balansingiz yetmaydi!", show_alert=True)
    return

  await state.update_data(
      selected_gift_id=gift_id, selected_gift_price=selected_gift["price"]
  )

  await callback.message.answer(
      "👤 Gift yuborilishi kerak bo'lgan foydalanuvchining **Telegram ID**"
      " raqamini yuboring:"
  )
  await state.set_state(GiftStates.waiting_for_user_id)
  await callback.answer()


@dp.message(GiftStates.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
  if not message.text.isdigit():
    await message.answer("Iltimos, to'g'ri Telegram ID raqamini kiriting:")
    return

  target_user_id = int(message.text)
  await state.update_data(target_user_id=target_user_id)

  await message.answer(
      "✍️ Gift bilan birga yuboriladigan matnni (xabarni) kiriting:"
  )
  await state.set_state(GiftStates.waiting_for_custom_text)


@dp.message(GiftStates.waiting_for_custom_text)
async def process_custom_text(message: types.Message, state: FSMContext):
  custom_text = message.text
  data = await state.get_data()
  target_user_id = data.get("target_user_id")
  gift_id = data.get("selected_gift_id")
  price = data.get("selected_gift_price")
  await state.clear()

  if DATABASE["bot_balance"] < price:
    await message.answer(
        "❌ Xatolik: Balansingizda yetarli stars qolmagan!"
    )
    return

  try:
    DATABASE["bot_balance"] -= price

    await bot.send_gift(
        user_id=target_user_id, gift_id=gift_id, text=custom_text
    )
    await message.answer(
        f"✅ Gift ID: `{target_user_id}` ga muvaffaqiyatli yuborildi!"
    )
  except Exception as e:
    DATABASE["bot_balance"] += price
    await message.answer(f"❌ Gift yuborishda xatolik yuz berdi: {e}")


@dp.callback_query(F.data == "back_to_admin")
async def back_admin(callback: types.CallbackQuery):
  if callback.from_user.id != ADMIN_ID:
    return
  keyboard = InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(text="🎁 Gift yechish", callback_data="admin_gifts")],
      [
          InlineKeyboardButton(
              text="📊 Statistika", callback_data="admin_stats"
          )
      ],
  ])
  await callback.message.edit_text(
      "👑 Admin panelga xush kelibsiz:", reply_markup=keyboard
  )


async def main():
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
