import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.cryptobot import CryptoBotClient
import aiohttp

@pytest.mark.asyncio
async def test_cryptobot_get_me():
    client = CryptoBotClient("test_token", testnet=True)
    
    mock_response = {
        "ok": True,
        "result": {"app_id": 1, "name": "TestBot"}
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_ctx = MagicMock()
        mock_ctx.__aenter__.return_value = MagicMock(json=AsyncMock(return_value=mock_response))
        mock_request.return_value = mock_ctx
        
        result = await client.get_me()
        assert result["name"] == "TestBot"

@pytest.mark.asyncio
async def test_cryptobot_create_invoice():
    client = CryptoBotClient("test_token", testnet=True)
    
    mock_response = {
        "ok": True,
        "result": {"invoice_id": 123, "pay_url": "https://t.me/cryptobot?start=123"}
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_ctx = MagicMock()
        mock_ctx.__aenter__.return_value = MagicMock(json=AsyncMock(return_value=mock_response))
        mock_request.return_value = mock_ctx
        
        result = await client.create_invoice(10.0)
        assert result["invoice_id"] == 123
        assert result["pay_url"] is not None

@pytest.mark.asyncio
async def test_cryptobot_get_invoices():
    client = CryptoBotClient("test_token", testnet=True)
    
    mock_response = {
        "ok": True,
        "result": {"items": [{"invoice_id": 123, "status": "paid"}]}
    }
    
    with patch('aiohttp.ClientSession.request') as mock_request:
        mock_ctx = MagicMock()
        mock_ctx.__aenter__.return_value = MagicMock(json=AsyncMock(return_value=mock_response))
        mock_request.return_value = mock_ctx
        
        result = await client.get_invoices(status="paid")
        assert result["items"][0]["status"] == "paid"
