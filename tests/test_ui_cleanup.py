import pytest
from unittest.mock import AsyncMock, MagicMock
from app.bot.handlers.common import start_cmd, my_subscription_handler
from aiogram.types import Message, CallbackQuery

def has_known_emojis(text):
    known_emojis = ["✅", "❌", "⚠️", "🚫", "⏳", "👤", "📊", "💾", "📅", "💡", "🛡️", "🔗"]
    return any(emoji in text for emoji in known_emojis)

@pytest.mark.asyncio
async def test_start_cmd_no_emojis():
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.full_name = "Test User"
    message.answer = AsyncMock()
    
    db = AsyncMock()
    db.get_user.return_value = {"telegram_id": 123, "balance": 0.0, "group_name": "Standard"}
    
    await start_cmd(message, db)
    
    args, kwargs = message.answer.call_args
    text = args[0]
    kb = kwargs['reply_markup']
    
    # Check for known emojis (this should fail before implementation)
    assert not has_known_emojis(text)
    for row in kb.inline_keyboard:
        for button in row:
            assert not has_known_emojis(button.text)
            
    # Check specific renames
    button_texts = [b.text for row in kb.inline_keyboard for b in row]
    assert "Мои услуги" in button_texts
    assert "Партнерская программа" in button_texts

@pytest.mark.asyncio
async def test_my_subscription_no_emojis():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.message.photo = None
    
    db = AsyncMock()
    db.get_user.return_value = {"telegram_id": 123, "marzban_username": "123_test"}
    
    marzban = AsyncMock()
    m_user = MagicMock()
    m_user.username = "123_test"
    m_user.status = "active"
    m_user.used_traffic = 0
    m_user.data_limit = 0
    m_user.expire = 0
    m_user.subscription_url = "http://sub"
    marzban.get_user.return_value = m_user
    
    await my_subscription_handler(callback, db, marzban)
    
    args, kwargs = callback.message.edit_text.call_args
    text = args[0]
    kb = kwargs['reply_markup']
    
    assert not has_known_emojis(text)
    for row in kb.inline_keyboard:
        for button in row:
            assert not has_known_emojis(button.text)