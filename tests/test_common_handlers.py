import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.handlers.common import start_cmd, check_subscription_handler, my_subscription_handler, support_handler, get_qr_handler, checkout_handler, referral_menu
from aiogram.types import Message, CallbackQuery, ChatMemberMember, ChatMemberLeft

@pytest.mark.asyncio
async def test_start_cmd():
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.full_name = "Test User"
    message.answer = AsyncMock()
    
    db = AsyncMock()
    db.get_user.return_value = {"telegram_id": 123, "balance": 0.0, "group_name": "Standard"}
    
    await start_cmd(message, db)
    message.answer.assert_called()
    assert "Привет, Test User" in message.answer.call_args[0][0]
    assert "Баланс: 0.0" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_check_subscription_handler_success():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.from_user.username = "testuser"
    callback.from_user.full_name = "testuser"
    callback.answer = AsyncMock()
    callback.message = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.bot.get_chat_member = AsyncMock(return_value=AsyncMock(spec=ChatMemberMember, status="member"))
    
    db = AsyncMock()
    db.get_user.return_value = {"telegram_id": 123, "balance": 0.0}
    
    with patch('os.getenv', return_value="@test_channel"):
        await check_subscription_handler(callback, db)
    
    db.add_user.assert_called_with(123, "testuser")
    callback.answer.assert_called_with("Подписка подтверждена")
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
    callback.answer.assert_called_with("Вы не подписаны на канал")

@pytest.mark.asyncio
async def test_my_subscription_handler_success():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    
    db = AsyncMock()
    marzban = AsyncMock()
    # Mock Marzban user response
    m_user = MagicMock()
    m_user.username = "user_123"
    m_user.status = "active"
    m_user.used_traffic = 1024**3
    m_user.data_limit = 5 * 1024**3
    m_user.expire = "2026-01-01"
    m_user.subscription_url = "/sub/test"
    marzban.get_user.return_value = m_user
    
    with patch('os.getenv', side_effect=lambda k, d=None: "https://vpn.lol" if k == "SUB_URL_PREFIX" else d):
        await my_subscription_handler(callback, db, marzban)
    
    callback.message.edit_text.assert_called()
    args, kwargs = callback.message.edit_text.call_args
    assert "Ваша подписка:" in args[0]
    
    # Check button URLs
    kb = kwargs['reply_markup']
    # index 0: Renew, 1: Open Browser, 2: v2rayTun, 3: Streisand
    assert kb.inline_keyboard[2][0].text == "v2rayTun"
    assert "v2raytun://import/https://vpn.lol/sub/test" == kb.inline_keyboard[2][0].url

@pytest.mark.asyncio
async def test_support_handler():
    callback = AsyncMock(spec=CallbackQuery)
    callback.message = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    
    await support_handler(callback)
    callback.message.answer.assert_called_with("Для связи с поддержкой напишите @renkaa1")

@pytest.mark.asyncio
async def test_get_qr_handler_success():
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "get_qr:user_123"
    callback.message = AsyncMock()
    callback.message.answer_photo = AsyncMock()
    callback.answer = AsyncMock()
    
    marzban = AsyncMock()
    m_user = MagicMock()
    m_user.username = "user_123"
    m_user.subscription_url = "https://link.com"
    marzban.get_user.return_value = m_user
    
    await get_qr_handler(callback, marzban)
    
    callback.message.answer_photo.assert_called()
    args, kwargs = callback.message.answer_photo.call_args
    assert "user_123" in kwargs['caption']
    callback.answer.assert_called_once()

@pytest.mark.asyncio
async def test_referral_menu():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    
    # Mock bot.get_me for username
    callback.bot.get_me = AsyncMock(return_value=MagicMock(username="bot_user"))
    
    db = AsyncMock()
    db.get_referral_count.return_value = 5
    
    await referral_menu(callback, db)
    
    callback.message.edit_text.assert_called()
    args, kwargs = callback.message.edit_text.call_args
    assert "Приглашено: 5 чел." in args[0]
    assert "start=123" in args[0]

@pytest.mark.asyncio
async def test_checkout_handler_top_up():
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "checkout:buy:7:50"
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    
    db = AsyncMock()
    db.get_user.return_value = {"telegram_id": 123, "balance": 0.0} # Low balance
    
    crypto = AsyncMock()
    crypto.get_exchange_rates.return_value = [{"source": "USDT", "target": "RUB", "rate": "100.0"}]
    crypto.create_invoice.return_value = {
        "invoice_id": 999,
        "pay_url": "https://pay.link"
    }
    
    marzban = AsyncMock()
    
    await checkout_handler(callback, db, marzban, crypto)
    
    crypto.create_invoice.assert_called()
    assert "Недостаточно средств" in callback.message.edit_text.call_args[0][0]