import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.handlers.common import start_cmd, check_subscription_handler
from aiogram.types import Message, CallbackQuery, ChatMemberMember, ChatMemberLeft

@pytest.mark.asyncio
async def test_start_cmd():
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.full_name = "Test User"
    message.answer = AsyncMock()
    
    await start_cmd(message)
    message.answer.assert_called()
    assert "Привет, Test User" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_check_subscription_handler_success():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.from_user.username = "testuser"
    callback.answer = AsyncMock()
    callback.message = AsyncMock()
    callback.bot.get_chat_member = AsyncMock(return_value=AsyncMock(spec=ChatMemberMember, status="member"))
    
    db = AsyncMock()
    
    with patch('os.getenv', return_value="@test_channel"):
        await check_subscription_handler(callback, db)
    
    db.add_user.assert_called_with(123, "testuser")
    callback.answer.assert_called_with("Подписка подтверждена! 🎉", show_alert=True)
    callback.message.delete.assert_called_once()

@pytest.mark.asyncio
async def test_check_subscription_handler_fail():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.answer = AsyncMock()
    callback.bot.get_chat_member = AsyncMock(return_value=AsyncMock(spec=ChatMemberLeft, status="left"))
    
    db = AsyncMock()
    
    with patch('os.getenv', return_value="@test_channel"):
        await check_subscription_handler(callback, db)
    
    db.add_user.assert_not_called()
    callback.answer.assert_called_with("Вы все еще не подписаны на канал!", show_alert=True)
