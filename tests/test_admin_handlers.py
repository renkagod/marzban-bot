import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.handlers.admin import admin_menu, manage_user_options, set_user_group
from aiogram.types import Message, CallbackQuery

@pytest.mark.asyncio
async def test_admin_menu_no_users():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock() # Explicitly make it AsyncMock
    db = AsyncMock()
    db.get_all_users.return_value = []
    
    await admin_menu(message, db)
    message.answer.assert_called_with("Пользователей пока нет.")

@pytest.mark.asyncio
async def test_admin_menu_with_users():
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    db = AsyncMock()
    db.get_all_users.return_value = [{"telegram_id": 123, "username": "test", "group_name": "Standard"}]
    
    await admin_menu(message, db)
    assert message.answer.called
    args, kwargs = message.answer.call_args
    assert "Выберите пользователя" in args[0]
    assert kwargs['reply_markup'] is not None

@pytest.mark.asyncio
async def test_set_user_group():
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "set_group:123:Inner Circle"
    callback.answer = AsyncMock()
    
    db = AsyncMock()
    db.get_user.return_value = {"telegram_id": 123, "username": "test", "group_name": "Inner Circle"}
    db.update_user_group = AsyncMock()
    
    # We need to mock edit_text since it calls manage_user_options
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    
    await set_user_group(callback, db)
    db.update_user_group.assert_called_with(123, "Inner Circle")
    callback.answer.assert_called_with("Группа изменена на Inner Circle")