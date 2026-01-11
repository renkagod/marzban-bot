from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.core.database import DatabaseManager
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.database import DatabaseManager
from app.core.marzban_client import MarzbanManager
from app.utils.qr import generate_qr_code
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("get_qr:"))
async def get_qr_handler(callback: CallbackQuery, marzban: MarzbanManager):
    marzban_username = callback.data.split(":")[1]
    
    try:
        m_user = await marzban.get_user(marzban_username)
        qr_file = generate_qr_code(m_user.subscription_url)
        
        await callback.message.answer_photo(
            photo=qr_file,
            caption=f"Ваш QR-код для подключения (<code>{m_user.username}</code>)"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error generating QR: {e}")
        await callback.answer("Ошибка при генерации QR-кода.", show_alert=True)

@router.message(Command("start"))
async def start_cmd(message: Message, db: DatabaseManager):
    user = await db.get_user(message.from_user.id)
    if not user:
        # Should be handled by middleware, but just in case
        await db.add_user(message.from_user.id, message.from_user.username)
        user = await db.get_user(message.from_user.id)

    text = (
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        f"💰 <b>Баланс:</b> {user['balance']} руб.\n"
        f"👥 <b>Группа:</b> {user['group_name']}\n\n"
        "Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Моя подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "my_subscription")
async def my_subscription_handler(callback: CallbackQuery, db: DatabaseManager, marzban: MarzbanManager):
    user = await db.get_user(callback.from_user.id)
    
    # In Marzban, user usually has a username. We can use telegram ID as username if we created them that way.
    # For now, let's try to get user by telegram ID (as string) or username.
    # Usually, we'll name the Marzban user like 'user_12345678'
    marzban_username = f"user_{callback.from_user.id}"
    
    try:
        m_user = await marzban.get_user(marzban_username)
        
        status_emoji = "🟢" if m_user.status == "active" else "🔴"
        
        text = (
            f"<b>Ваша подписка:</b>\n\n"
            f"👤 <b>Логин:</b> <code>{m_user.username}</code>\n"
            f"📡 <b>Статус:</b> {status_emoji} {m_user.status}\n"
            f"📊 <b>Трафик:</b> {round(m_user.used_traffic / (1024**3), 2)} ГБ / "
            f"{round(m_user.data_limit / (1024**3), 2) if m_user.data_limit else '∞'} ГБ\n"
            f"📅 <b>Истекает:</b> {m_user.expire if m_user.expire else 'Никогда'}\n\n"
            f"🔗 <b>Ссылка:</b> <code>{m_user.subscription_url}</code>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🖼 Получить QR-код", callback_data=f"get_qr:{marzban_username}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        await callback.answer("Подписка не найдена. Пополните баланс для активации.", show_alert=True)

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, db: DatabaseManager):
    user = await db.get_user(callback.from_user.id)
    
    text = (
        f"Привет, {callback.from_user.full_name}! 👋\n\n"
        f"💰 <b>Баланс:</b> {user['balance']} руб.\n"
        f"👥 <b>Группа:</b> {user['group_name']}\n\n"
        "Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Моя подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    await callback.answer("Для связи с поддержкой напишите @renkaa1", show_alert=True)

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
