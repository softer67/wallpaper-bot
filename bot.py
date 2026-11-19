import asyncio
import html
import logging
import re
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
                    callback_data=f"grant:{web_user_id}:{tg_user_id}:5",
                ),
                InlineKeyboardButton(
                    text="➕ 10 ген.",
                    callback_data=f"grant:{web_user_id}:{tg_user_id}:10",
                ),
                InlineKeyboardButton(
                    text="➕ 50 ген.",
                    callback_data=f"grant:{web_user_id}:{tg_user_id}:50",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="♾️ Безлимит",
                    callback_data=f"grant:{web_user_id}:{tg_user_id}:99999",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject:{web_user_id}:{tg_user_id}",
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
                "⏳ <b>Ваша заявка уже находится на рассмотрении!</b>\n\nПожалуйста, дожидайтесь ответа администратора.",
                parse_mode="HTML",
            )
            return

        admin_text = (
            "🔔 <b>Новая заявка на генерации!</b>\n\n"
            f"👤 <b>Пользователь:</b> {html.escape(full_name)} ({html.escape(username)})\n"
            f"🆔 <b>Telegram ID:</b> <code>{tg_user_id}</code>\n"
            f"💻 <b>ID / Юзернейм на сайте:</b> <code>{html.escape(web_user_id)}</code>\n\n"
            "Выберите, сколько генераций начислить:"
        )

        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                reply_markup=get_admin_keyboard(web_user_id, tg_user_id),
                parse_mode="HTML",
            )
            active_requests.add(web_user_id)
            await message.answer(
                "🎄 <b>Заявка успешно отправлена!</b>\n\n"
                f"Ваш ID на сайте: <code>{html.escape(web_user_id)}</code>\n"
                "Ожидайте ответа администратора.",
                parse_mode="HTML",
            )
        except Exception as e:
            logging.error(f"Ошибка отправки администратору: {e}")
            await message.answer(
                "⚠️ Не удалось доставить заявку администратору. Пожалуйста, попробуйте чуть позже.",
                parse_mode="HTML",
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
            "❄️ <b>Привет! Это официальный бот Студии Живых 4K Обоев.</b>\n\n"
            "Нажмите кнопку ниже или просто отправьте в чат ваш ID сайта (<code>user_...</code>, <code>usr_...</code>) либо ваш <code>@username</code>.",
            reply_markup=kb,
            parse_mode="HTML",
        )

# Обработка отправки ID или Telegram username (с @ или без, либо user_/usr_)
@dp.message(
    F.text & ~F.text.startswith("/") & (
        F.text.startswith(("user_", "usr_", "@")) |
        F.text.regexp(r"^[a-zA-Z0-9_]{3,32}$")
    )
)
async def process_text_id(message: types.Message):
    tg_user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    full_name = message.from_user.full_name
    web_user_id = message.text.strip()

    if web_user_id in active_requests:
        await message.answer("⏳ Ваша заявка уже на рассмотрении!", parse_mode="HTML")
        return

    admin_text = (
        "🔔 <b>Новая заявка на генерации!</b>\n\n"
        f"👤 <b>Пользователь:</b> {html.escape(full_name)} ({html.escape(username)})\n"
        f"🆔 <b>Telegram ID:</b> <code>{tg_user_id}</code>\n"
        f"💻 <b>ID / Юзернейм:</b> <code>{html.escape(web_user_id)}</code>\n\n"
        "Выберите, сколько генераций начислить:"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=get_admin_keyboard(web_user_id, tg_user_id),
            parse_mode="HTML",
        )
        active_requests.add(web_user_id)
        await message.answer(
            f"🎄 <b>Заявка отправлена!</b>\nID / Юзернейм: <code>{html.escape(web_user_id)}</code>\nОжидайте ответа администратора.",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки администратору: {e}")
        await message.answer(
            "⚠️ Не удалось доставить заявку администратору. Попробуйте еще раз через несколько секунд.",
            parse_mode="HTML"
        )

@dp.callback_query(F.data == "manual_id")
async def process_manual_id(callback: types.CallbackQuery):
    await callback.message.answer(
        "✍️ Отправьте ваш ID сайта (<code>user_...</code>, <code>usr_...</code>) или ваш Telegram <code>@username</code> в чат.",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("grant"))
async def process_grant(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    if ":" in callback.data:
        parts = callback.data.split(":")
        web_user_id = parts[1]
        tg_user_id = int(parts[2])
        amount = parts[3]
    else:
        parts = callback.data.split("_")
        amount = parts[-1]
        tg_user_id = int(parts[-2])
        web_user_id = "_".join(parts[1:-2])

    active_requests.discard(web_user_id)

    grant_display = "♾️ Безлимит" if amount == "99999" else f"{amount}"
    bonus_val = "unlimited" if amount == "99999" else amount
    bonus_url = f"https://fourk-wallpaper-site.onrender.com/?bonus={bonus_val}"

    # Кнопка для мгновенной активации генераций на сайте
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=f"🎁 Активировать {grant_display} на сайте",
                url=bonus_url,
            )
        ]]
    )

    await callback.message.edit_text(
        f"✅ Пользователю <code>{html.escape(web_user_id)}</code> одобрено {grant_display} генераций.",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            chat_id=tg_user_id,
            text=(
                f"🎉 <b>Вам начислено {grant_display} генераций для ID <code>{html.escape(web_user_id)}</code>!</b>\n\n"
                f"👇 Нажмите кнопку ниже, чтобы генерации активировались на сайте:"
            ),
            reply_markup=kb,
            parse_mode="HTML",
        )
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения пользователю: {e}")

    await callback.answer("Готово!")

@dp.callback_query(F.data.startswith("reject"))
async def process_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    if ":" in callback.data:
        parts = callback.data.split(":")
        web_user_id = parts[1]
        tg_user_id = int(parts[2])
    else:
        parts = callback.data.split("_")
        tg_user_id = int(parts[-1])
        web_user_id = "_".join(parts[1:-1])

    active_requests.discard(web_user_id)

    await callback.message.edit_text(
        f"❌ Заявка отклонена (<code>{html.escape(web_user_id)}</code>).",
        parse_mode="HTML"
    )
    try:
        await bot.send_message(tg_user_id, "😔 Администратор отклонил ваш запрос.")
    except Exception:
        pass

    await callback.answer("Отклонено")

# Команда для сброса зависших заявок: /clear
@dp.message(Command("clear", "reset"))
async def cmd_clear(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = len(active_requests)
    active_requests.clear()
    await message.answer(f"🧹 Очищено {count} активных заявок.", parse_mode="HTML")

# Команда для администратора: /give @username 50
@dp.message(Command("give", "grant"))
async def cmd_give(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "Формат команды:\n<code>/give &lt;ID или @username&gt; &lt;кол-во&gt;</code>\nНапример: <code>/give @Benjamin_Bobbie 50</code>",
            parse_mode="HTML"
        )
        return

    target = args[1]
    amount = args[2]
    bonus_url = f"https://fourk-wallpaper-site.onrender.com/?bonus={amount}"
    await message.answer(
        f"✅ Начислено {amount} генераций для <code>{html.escape(target)}</code>!\nСсылка для активации:\n{bonus_url}",
        parse_mode="HTML"
    )

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

# Запуск бота
async def main():
    await web_server()
    print("🚀 Бот и веб-сервер успешно запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
