from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.database import DatabaseManager
import os

router = Router()

def is_admin(message: Message):
    # Simplest check: compare with ADMIN_CHANNEL_ID or a list of IDs
    # For now, let's assume we use an ADMIN_ID from env
    admin_id = os.getenv("ADMIN_ID")
    return str(message.from_user.id) == str(admin_id)

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Я бот для управления Marzban.\n\n"
        "Используйте кнопки меню для навигации."
    )

@router.message(Command("admin"))
async def admin_menu(message: Message, db: DatabaseManager):
    # Проверка на админа
    admin_id = os.getenv("ADMIN_ID")
    if str(message.from_user.id) != str(admin_id):
        return # Просто игнорируем, если не админ

    users = await db.get_all_users()
    
    if not users:
        await message.answer("Пользователей пока нет.")
        return

    keyboard = []
    for user in users:
        group = user['group_name']
        text = f"{user['username'] or user['telegram_id']} ({group})"
        keyboard.append([InlineKeyboardButton(
            text=text, 
            callback_data=f"manage_user:{user['telegram_id']}"
        )])
    
    await message.answer(
        "Выберите пользователя для управления группой:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("manage_user:"))
async def manage_user_options(callback: CallbackQuery, db: DatabaseManager):
    user_id = int(callback.data.split(":")[1])
    user = await db.get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton(text="Сделать Standard", callback_data=f"set_group:{user_id}:Standard")],
        [InlineKeyboardButton(text="Сделать Inner Circle", callback_data=f"set_group:{user_id}:Inner Circle")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_back")]
    ]
    
    await callback.message.edit_text(
        f"Управление пользователем {user['username'] or user_id}\nТекущая группа: {user['group_name']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("set_group:"))
async def set_user_group(callback: CallbackQuery, db: DatabaseManager):
    _, user_id, group_name = callback.data.split(":")
    user_id = int(user_id)
    
    await db.update_user_group(user_id, group_name)
    await callback.answer(f"Группа изменена на {group_name}")
    
    # Refresh menu
    await manage_user_options(callback, db)
