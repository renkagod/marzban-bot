import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.handlers.common import start_cmd
from aiogram.types import Message, InlineKeyboardMarkup

@pytest.mark.asyncio
async def test_main_menu_with_db_data():
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.full_name = "Test User"
    message.answer = AsyncMock()
    
    db = AsyncMock()
    db.get_user.return_value = {
        "telegram_id": 123,
        "username": "testuser",
        "group_name": "Standard",
        "balance": 150.0
    }
    
    # We update start_cmd to use db
    await start_cmd(message, db)
    
    args, kwargs = message.answer.call_args
    text = args[0]
    assert "Баланс: 150.0" in text
    assert "Standard" not in text # Hidden from UI
    assert kwargs['reply_markup'] is not None
