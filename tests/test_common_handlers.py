import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.handlers.common import start_cmd, check_subscription_handler, my_subscription_handler, support_handler, get_qr_handler, top_up_menu, create_invoice_handler, referral_menu
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
    assert "Баланс:</b> 0.0" in message.answer.call_args[0][0]

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
    
    # Check button URL
    kb = kwargs['reply_markup']
    assert kb.inline_keyboard[0][0].url == "https://vpn.lol/sub/test"

@pytest.mark.asyncio
async def test_support_handler():
    callback = AsyncMock(spec=CallbackQuery)
    callback.answer = AsyncMock()
    
    await support_handler(callback)
    callback.answer.assert_called_with("Для связи с поддержкой напишите @renkaa1", show_alert=True)

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
async def test_top_up_menu():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    
    db = AsyncMock()
    db.get_user.return_value = {"telegram_id": 123, "group_name": "Inner Circle"}
    
    with patch('os.getenv', side_effect=lambda k, d=None: "150" if k == "PRICE_INNER_CIRCLE" else d):
        await top_up_menu(callback, db)
    
    callback.message.edit_text.assert_called()
    assert "150 руб." in callback.message.edit_text.call_args[0][0]
    assert "Inner Circle" in callback.message.edit_text.call_args[0][0]

@pytest.mark.asyncio
async def test_create_invoice_handler_success():
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "buy:150"
    callback.from_user = MagicMock()
    callback.from_user.id = 123
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    
    db = AsyncMock()
    crypto = AsyncMock()
    crypto.get_exchange_rates.return_value = [{"source": "USDT", "target": "RUB", "rate": "100.0"}]
    crypto.create_invoice.return_value = {
        "invoice_id": 999,
        "pay_url": "https://pay.link"
    }
    
    # No need to mock bot.dp anymore as it's passed directly
    await create_invoice_handler(callback, db, crypto)
    
    crypto.create_invoice.assert_called()
    db.add_payment.assert_called_with(
        telegram_id=123,
        amount=150.0,
        provider="CryptoBot",
        external_id="999"
    )
    assert "Счет на 150.0 руб." in callback.message.edit_text.call_args[0][0]
    assert "USDT) создан" in callback.message.edit_text.call_args[0][0]

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
