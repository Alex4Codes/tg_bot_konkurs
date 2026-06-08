import asyncio
import html
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.exceptions import TelegramAPIError

from src.config import settings
from src.database import init_db, add_participant, get_participants_count

# Безопасное логирование: избегаем PII в продакшен-логах
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота (без запуска сессии здесь)
bot = Bot(token=settings.bot_token)
dp = Dispatcher()

# Список админов (лучше вынести в settings)
ADMIN_IDS = getattr(settings, 'admin_ids', [settings.admin_id])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я подписался, проверить участие", callback_data="check_participation")]
    ])
    
    # Используем HTML и экранируем данные пользователя!
    safe_name = html.escape(message.from_user.full_name)
    safe_channel = html.escape(settings.channel_id)
    
    await message.answer(
        f"👋 Привет, {safe_name}!\n\n"
        f"🏆 Для участия в конкурсе необходимо:\n"
        f"1️⃣ Быть подписанным на канал: {safe_channel}\n"
        f"2️⃣ Нажать кнопку ниже.\n\n"
        f"⚠️ Не отписывайтесь до подведения итогов, иначе участие будет аннулировано.",
        reply_markup=keyboard,
        parse_mode="HTML" # Сменили на HTML
    )

@dp.callback_query(F.data == "check_participation")
async def check_participation(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Нет_username"
    full_name = callback.from_user.full_name

    # Отвечаем на коллбэк сразу, чтобы убрать часики у пользователя
    await callback.answer()

    try:
        # 1. Проверяем подписку через Telegram API
        member = await bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)
        
        # Корректная проверка: участник - это любой, кто не ушел и не забанен
        if member.status not in ["left", "kicked"]:
            # 2. Если подписан, пытаемся добавить в БД
            is_new = await add_participant(user_id, username, full_name)
            
            if is_new:
                logger.info(f"Новый участник: {user_id}") # Убрали PII из логов
                
                safe_name = html.escape(full_name)
                await callback.message.edit_text(
                    f"🎉 Поздравляем, {safe_name}!\n\n"
                    f"✅ Подписка подтверждена.\n"
                    f"✅ Вы успешно зарегистрированы в конкурсе!\n\n"
                    f"Ждите результатов. Удачи! 🍀",
                    parse_mode="HTML"
                )
                
                # Безопасное уведомление админу
                safe_username = html.escape(username)
                safe_name_admin = html.escape(full_name)
                await bot.send_message(
                    settings.admin_id, 
                    f"🆕 Новый участник: @{safe_username} (ID: <code>{user_id}</code>, Имя: {safe_name_admin})",
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text("Вы уже зарегистрированы в конкурсе! 🎉")
        else:
            logger.info(f"Пользователь {user_id} не подписан (статус: {member.status})")
            await callback.message.edit_text("❌ Вы не подписаны на канал! Подпишитесь и попробуйте снова.")
            
    except TelegramAPIError as e:
        logger.error(f"Ошибка API Telegram для {user_id}: {e}")
        await callback.message.edit_text("⚠️ Ошибка проверки. Попробуйте позже или обратитесь к админу.")
    except Exception as e:
        logger.exception(f"Непредвиденная ошибка для {user_id}")
        await callback.message.edit_text("Произошла техническая ошибка. Мы уже работаем над её исправлением.")

# Защита админских команд
@dp.message(F.text == "/stats", F.from_user.id.in_(ADMIN_IDS))
async def cmd_stats(message: Message):
    """Команда для админа: показать количество участников"""
    count = await get_participants_count()
    await message.answer(f"📊 Всего участников в конкурсе: {count}")

async def main():
    logger.info("Инициализация базы данных...")
    await init_db()
    
    logger.info("Запуск бота...")
    # drop_pending_updates=True защищает от повторной обработки старых сообщений при падении бота
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем")
    # Примечание: в aiogram v3 при использовании asyncio.run(dp.start_polling)
    # сессия бота закрывается автоматически корутиной Dispatcher.
