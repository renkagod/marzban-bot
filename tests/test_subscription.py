import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.middlewares.subscription import SubscriptionMiddleware
from aiogram.types import Message, ChatMemberMember, ChatMemberLeft

@pytest.mark.asyncio
async def test_subscription_middleware_with_referral():
    middleware = SubscriptionMiddleware(channel_id="@test_channel")
    handler = AsyncMock(return_value="success")
    event = AsyncMock(spec=Message)
    event.from_user = MagicMock()
    event.from_user.id = 123
    event.from_user.username = "newuser"
    event.text = "/start 456" # Referred by 456
    event.bot.get_chat_member = AsyncMock(return_value=AsyncMock(spec=ChatMemberMember, status="member"))
    
    db = AsyncMock()
    db.get_user.return_value = None
    data = {"db": db}
    
    with patch('os.getenv', return_value="https://t.me/invite"):
        await middleware(handler, event, data)
    
    db.add_user.assert_called_with(123, "newuser", referred_by=456)

@pytest.mark.asyncio
async def test_subscription_middleware_not_subscribed():
    middleware = SubscriptionMiddleware(channel_id="@test_channel")
    handler = AsyncMock()
    event = AsyncMock(spec=Message)
    event.from_user = MagicMock()
    event.from_user.id = 123
    event.from_user.username = "testuser"
    event.bot.get_chat_member = AsyncMock(return_value=AsyncMock(spec=ChatMemberLeft, status="left"))
    event.answer = AsyncMock()
    data = {"db": AsyncMock()}
    data["db"].get_user = AsyncMock(return_value=None) # First time user
    
    with patch('os.getenv', return_value="https://t.me/invite"):
        result = await middleware(handler, event, data)
    
    assert result is None
    handler.assert_not_called()
    event.answer.assert_called()
    assert "подписаться" in event.answer.call_args[0][0].lower()
