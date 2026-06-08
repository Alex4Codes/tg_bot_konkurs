import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.exceptions import TelegramAPIError

from src.config import settings
from src.database import init_db, add_participant, get_participants_count

# Настройка логирования для продакшена (вывод в консоль и файл)
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я подписался, проверить участие", callback_data="check_participation")]
    ])
    
    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        f"🏆 Для участия в конкурсе необходимо:\n"
        f"1️⃣ Быть подписанным на канал: {settings.channel_id}\n"
        f"2️⃣ Нажать кнопку ниже.\n\n"
        f"⚠️ *Не отписывайтесь до подведения итогов, иначе участие будет аннулировано.*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_participation")
async def check_participation(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Нет username"
    full_name = callback.from_user.full_name

    try:
        # 1. Проверяем подписку через Telegram API
        member = await bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)
        
        if member.status in ["member", "administrator", "creator"]:
            # 2. Если подписан, пытаемся добавить в БД
            is_new = await add_participant(user_id, username, full_name)
            
            if is_new:
                logger.info(f"Новый участник: {user_id} (@{username})")
                await callback.message.edit_text(
                    f"🎉 Поздравляем, {full_name}!\n\n"
                    f"✅ Подписка подтверждена.\n"
                    f"✅ Вы успешно зарегистрированы в конкурсе!\n\n"
                    f"Ждите результатов. Удачи! 🍀"
                )
                # Уведомление админу
                await bot.send_message(
                    settings.admin_id, 
                    f"🆕 Новый участник: @{username} (ID: `{user_id}`, Имя: {full_name})",
                    parse_mode="Markdown"
                )
            else:
                await callback.answer("Вы уже зарегистрированы в конкурсе! 🎉", show_alert=True)
        else:
            logger.warning(f"Пользователь {user_id} не подписан на канал (статус: {member.status})")
            await callback.answer("❌ Вы не подписаны на канал! Подпишитесь и попробуйте снова.", show_alert=True)
            
    except TelegramAPIError as e:
        logger.error(f"Ошибка API Telegram для пользователя {user_id}: {e}")
        await callback.answer("⚠️ Ошибка проверки. Попробуйте позже или обратитесь к админу.", show_alert=True)
    except Exception as e:
        logger.exception(f"Непредвиденная ошибка для пользователя {user_id}: {e}")
        await callback.answer("Произошла техническая ошибка. Мы уже работаем над её исправлением.", show_alert=True)

@dp.message(F.text == "/stats", F.from_user.id == settings.admin_id)
async def cmd_stats(message: Message):
    """Команда для админа: показать количество участников"""
    count = await get_participants_count()
    await message.answer(f"📊 Всего участников в конкурсе: {count}")

async def main():
    logger.info("Инициализация базы данных...")
    await init_db()
    
    logger.info("Запуск бота...")
    # drop_pending_updates=True игнорирует сообщения, накопившиеся пока бот был выключен
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
    finally:
        # Гарантированное закрытие сессии бота при завершении
        if bot.session.is_connected:
            asyncio.run(bot.session.close())
