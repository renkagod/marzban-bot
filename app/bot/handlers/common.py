from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.core.database import DatabaseManager
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Я бот для управления Marzban.\n\n"
        "Используйте кнопки меню для навигации."
    )

@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery, db: DatabaseManager):
    user_id = callback.from_user.id
    channel_id = os.getenv("CHANNEL_ID")
    
    if not channel_id:
        await callback.answer("Ошибка конфигурации: CHANNEL_ID не задан.")
        return

    try:
        member = await callback.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            # Register user in DB
            await db.add_user(user_id, callback.from_user.username)
            await callback.answer("Подписка подтверждена! 🎉", show_alert=True)
            await callback.message.delete()
            # Optionally send /start message again or main menu
        else:
            await callback.answer("Вы все еще не подписаны на канал!", show_alert=True)
    except Exception as e:
        logger.error(f"Error checking subscription in handler: {e}")
        await callback.answer("Произошла ошибка при проверке. Попробуйте позже.")
