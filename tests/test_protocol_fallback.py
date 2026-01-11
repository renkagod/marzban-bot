import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.bot.handlers.common import process_subscription_action
from aiogram.types import User

@pytest.mark.asyncio
async def test_process_subscription_action_protocol_fallback():
    user_id = 123
    event_user = MagicMock(spec=User)
    event_user.id = user_id
    event_user.username = "test"
    event_user.full_name = "Test"
    
    db = AsyncMock()
    db.get_user.return_value = {"marzban_username": "123_test"}
    
    marzban = AsyncMock()
    # First call to get_user (check if exists) returns 404/Exception
    marzban.get_user.side_effect = Exception("404 Not Found")
    
    # First call to create_user fails with 400 Bad Request
    error_400 = Exception("400 Bad Request: VMess disabled")
    marzban.create_user.side_effect = [error_400, {"username": "123_test"}]
    
    await process_subscription_action(user_id, "buy", 30, marzban, event_user, db)
    
    # Verify create_user was called twice
    assert marzban.create_user.call_count == 2
    
    # First call had vmess
    first_call_args = marzban.create_user.call_args_list[0][0][0]
    assert "vmess" in first_call_args['proxies']
    
    # Second call (fallback) only has vless
    second_call_args = marzban.create_user.call_args_list[1][0][0]
    assert "vless" in second_call_args['proxies']
    assert "vmess" not in second_call_args['proxies']
