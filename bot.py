import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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


# Обработка команды /start (в том числе с параметром ?start=user_xxxxx или ?usr_xxxxx с сайта)
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    tg_user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    full_name = message.from_user.full_name

    # Проверяем, передан ли ID с сайта через /start
    args = message.text.split()
    if len(args) > 1:
        web_user_id = args[1].strip()

        # Защита от спама заявками
        if web_user_id in active_requests:
            await message.answer(
                "⏳ **Ваша заявка уже находится на рассмотрении!**\n\nПожалуйста, "
                "дождитесь ответа администратора. Как только генерации будут "
                "начислены, я сразу пришлю уведомление сюда.",
                parse_mode="Markdown",
            )
            return

        active_requests.add(web_user_id)

        # Ответ пользователю
        await message.answer(
            "🎄 **Заявка успешно отправлена!**\n\n"
            f"Ваш ID на сайте: `{web_user_id}`\n"
            "Ожидайте ответа администратора — обычно это занимает пару минут. "
            "Я пришлю уведомление прямо в этот чат, как только доступ будет открыт!",
            parse_mode="Markdown",
        )

        # Отправка уведомления Админу
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
        # Если юзер запустил бота просто так (Приветствие)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="📝 Отправить ID вручную", callback_data="manual_id"
                )
            ]]
        )
        await message.answer(
            "❄️ **Привет! Это официальный бот Студии Живых 4K Обоев.**\n\n"
            "Если у вас закончились бесплатные генерации на сайте, перейдите туда "
            "и нажмите кнопку **«Запросить генерации»** — заявка оформится автоматически.",
            reply_markup=kb,
            parse_mode="Markdown",
        )


# Обработка ID, отправленного простым текстом (поддерживает и user_, и usr_)
@dp.message(F.text.startswith(("user_", "usr_")))
async def process_text_id(message: types.Message):
    tg_user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"
    full_name = message.from_user.full_name
    web_user_id = message.text.strip()

    # Защита от спама заявками
    if web_user_id in active_requests:
        await message.answer(
            "⏳ **Ваша заявка уже находится на рассмотрении!**\n\nПожалуйста, "
            "дождитесь ответа администратора. Как только генерации будут "
            "начислены, я сразу пришлю уведомление сюда.",
            parse_mode="Markdown",
        )
        return

    active_requests.add(web_user_id)

    # Ответ пользователю
    await message.answer(
        "🎄 **Заявка успешно отправлена!**\n\n"
        f"Ваш ID на сайте: `{web_user_id}`\n"
        "Ожидайте ответа администратора — обычно это занимает пару минут. "
        "Я пришлю уведомление прямо в этот чат, как только доступ будет открыт!",
        parse_mode="Markdown",
    )

    # Отправка уведомления Админу
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


# Обработка нажатия кнопки «Отправить ID вручную»
@dp.callback_query(F.data == "manual_id")
async def process_manual_id(callback: types.CallbackQuery):
    await callback.message.answer(
        "✍️ **Введите ваш ID вручную:**\n\n"
        "Пожалуйста, отправьте ID в чат (он должен начинаться с `user_` или `usr_`), "
        "чтобы я мог зарегистрировать заявку.",
        parse_mode="Markdown"
    )
    await callback.answer()


# Обработка нажатия кнопок начисления генераций (grant_)
@dp.callback_query(F.data.startswith("grant_"))
async def process_grant(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    amount = parts[-1]
    tg_user_id = int(parts[-2])
    web_user_id = "_".join(parts[1:-2])

    active_requests.discard(web_user_id)

    await callback.message.edit_text(
        f"✅ Готово! Пользователю `{web_user_id}` одобрено **{amount}** генераций.",
        parse_mode="Markdown",
    )

    try:
        await bot.send_message(
            chat_id=tg_user_id,
            text=(
                "🎉 **Администратор одобрил ваш запрос!**\n\n🎁 Вам начислено:"
                f" **{amount}** генераций для ID `{web_user_id}`. Возвращайтесь на сайт! ❄️"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"Ошибка отправки пользователю: {e}")

    await callback.answer("Генерации начислены!")


# Отклонение заявки (reject_)
@dp.callback_query(F.data.startswith("reject_"))
async def process_reject(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    parts = callback.data.split("_")
    tg_user_id_str = parts[-1]
    web_user_id = "_".join(parts[1:-1])

    active_requests.discard(web_user_id)

    await callback.message.edit_text(
        f"❌ **Заявка отклонена** (ID: `{web_user_id}`).", 
        parse_mode="Markdown"
    )
    
    try:
        await bot.send_message(
            int(tg_user_id_str),
            "😔 К сожалению, администратор отклонил ваш запрос.",
        )
    except Exception:
        pass
    
    await callback.answer("Заявка отклонена")


# Запуск бота
async def main():
    print("🚀 Бот на aiogram успешно запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
