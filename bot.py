import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# ==========================================
# НАСТРОЙКИ БОТА
# ==========================================
TOKEN = "9177937588:AAFEdgj5Zs4w5xkSclSKGbibKRSM6KejWiE"
ADMIN_ID = 6493650695  # Твой числовой Telegram ID
# ==========================================

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Хранилище активных заявок, чтобы не было дублей
active_requests = set()

# Клавиатура для администратора под каждой заявкой
def get_admin_keyboard(web_user_id: str, tg_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ 5 ген.",
                    callback_data=f"grant_{web_user_id}_{tg_user_id}_5",
                ),
                InlineKeyboardButton(
                    text="➕ 10 ген.",
                    callback_data=f"grant_{web_user_id}_{tg_user_id}_10",
                ),
                InlineKeyboardButton(
                    text="➕ 50 ген.",
                    callback_data=f"grant_{web_user_id}_{tg_user_id}_50",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="♾️ Безлимит",
                    callback_data=f"grant_{web_user_id}_{tg_user_id}_99999",
                ),
                InlineKeyboardButton(
                    text="✏️ Свое число",
                    callback_data=f"custom_{web_user_id}_{tg_user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_{web_user_id}_{tg_user_id}",
                )
            ],
        ]
    )

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    tg_user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    full_name = message.from_user.full_name

    args = message.text.split()
    if len(args) > 1:
        web_user_id = args[1].strip()

        if web_user_id in active_requests:
            await message.answer(
                "⏳ **Ваша заявка уже находится на рассмотрении!**\n\nПожалуйста, дожидайтесь ответа администратора.",
                parse_mode="Markdown",
            )
            return

        active_requests.add(web_user_id)

        await message.answer(
            "🎄 **Заявка успешно отправлена!**\n\n"
            f"Ваш ID на сайте: `{web_user_id}`\n"
            "Ожидайте ответа администратора.",
            parse_mode="Markdown",
        )

        admin_text = (
            "🔔 **Новая заявка на генерации!**\n\n"
            f"👤 **Пользователь:** {full_name} ({username})\n"
            f"🆔 **Telegram ID:** `{tg_user_id}`\n"
            f"💻 **ID на сайте:** `{web_user_id}`\n\n"
            "Выберите, сколько генераций начислить:"
        )
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=get_admin_keyboard(web_user_id, tg_user_id),
            parse_mode="Markdown",
        )
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="📝 Отправить ID вручную", callback_data="manual_id"
                )
            ]]
        )
        await message.answer(
            "❄️ **Привет! Это официальный бот Студии Живых 4K Обоев.**",
            reply_markup=kb,
            parse_mode="Markdown",
        )

@dp.message(F.text.startswith(("user_", "usr_")))
async def process_text_id(message: types.Message):
    tg_user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    full_name = message.from_user.full_name
    web_user_id = message.text.strip()

    if web_user_id in active_requests:
        await message.answer("⏳ Ваша заявка уже на рассмотрении!", parse_mode="Markdown")
        return

    active_requests.add(web_user_id)

    await message.answer(f"🎄 Заявка отправлена! ID: `{web_user_id}`", parse_mode="Markdown")

    admin_text = (
        "🔔 **Новая заявка!**\n\n"
        f"👤 {full_name} ({username})\n"
        f"🆔 `{tg_user_id}`\n"
        f"💻 `{web_user_id}`"
    )
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        reply_markup=get_admin_keyboard(web_user_id, tg_user_id),
        parse_mode="Markdown",
    )

@dp.callback_query(F.data == "manual_id")
async def process_manual_id(callback: types.CallbackQuery):
    await callback.message.answer("✍️ Отправьте ваш ID (`user_...` или `usr_...`) в чат.")
    await callback.answer()

@dp.callback_query(F.data.startswith("grant_"))
async def process_grant(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    amount = parts[-1]
    tg_user_id = int(parts[-2])
    web_user_id = "_".join(parts[1:-2])

    active_requests.discard(web_user_id)

    await callback.message.edit_text(f"✅ Пользователю `{web_user_id}` одобрено {amount} генераций.", parse_mode="Markdown")

    try:
        await bot.send_message(
            chat_id=tg_user_id,
            text=f"🎉 Вам начислено **{amount}** генераций для ID `{web_user_id}`!",
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"Ошибка: {e}")

    await callback.answer("Готово!")

@dp.callback_query(F.data.startswith("reject_"))
async def process_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    tg_user_id_str = parts[-1]
    web_user_id = "_".join(parts[1:-1])

    active_requests.discard(web_user_id)

    await callback.message.edit_text(f"❌ Заявка отклонена (`{web_user_id}`).", parse_mode="Markdown")
    try:
        await bot.send_message(int(tg_user_id_str), "😔 Администратор отклонил ваш запрос.")
    except Exception:
        pass
    
    await callback.answer("Отклонено")

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (чтобы не было ошибки портов) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

async def main():
    # Запускаем веб-сервер и бота одновременно
    await web_server()
    print("🚀 Бот и веб-сервер успешно запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
