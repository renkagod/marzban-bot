import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.monitor import HealthMonitor

@pytest.mark.asyncio
async def test_monitor_alert_on_failure():
    marzban = AsyncMock()
    marzban.check_connectivity.return_value = False
    bot = AsyncMock()
    
    monitor = HealthMonitor(marzban, bot, "admin_id", interval=1)
    monitor.last_status = True # Initially OK
    
    await monitor.check()
    
    assert monitor.last_status is False
    bot.send_message.assert_called_once()
    assert "ВНИМАНИЕ" in bot.send_message.call_args[1]['text']

@pytest.mark.asyncio
async def test_monitor_alert_on_recovery():
    marzban = AsyncMock()
    marzban.check_connectivity.return_value = True
    bot = AsyncMock()
    
    monitor = HealthMonitor(marzban, bot, "admin_id", interval=1)
    monitor.last_status = False # Initially Down
    
    await monitor.check()
    
    assert monitor.last_status is True
    bot.send_message.assert_called_once()
    assert "снова в строю" in bot.send_message.call_args[1]['text']
