import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.core.marzban_client import MarzbanManager

@pytest.fixture
def config():
    return {
        "address": "https://example.com",
        "username": "admin",
        "password": "password"
    }

@patch("app.core.marzban_client.MarzbanAPI")
def test_marzban_init(mock_marzban, config):
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    assert manager.client is not None
    mock_marzban.assert_called_with(
        base_url=config["address"]
    )

@pytest.mark.asyncio
@patch("app.core.marzban_client.MarzbanAPI")
async def test_marzban_connectivity_success(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    # Mocking async methods
    mock_client.get_token = AsyncMock(return_value=MagicMock(access_token="test_token"))
    mock_client.get_system_stats = AsyncMock(return_value={"status": "running"})
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    assert await manager.check_connectivity() is True
    mock_client.get_token.assert_called_once_with(config["username"], config["password"])
    mock_client.get_system_stats.assert_called_once_with(token="test_token")

@pytest.mark.asyncio
@patch("app.core.marzban_client.MarzbanAPI")
async def test_marzban_connectivity_failure(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_token = AsyncMock(return_value=MagicMock(access_token="test_token"))
    mock_client.get_system_stats = AsyncMock(side_effect=Exception("Connection error"))
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    assert await manager.check_connectivity() is False

@pytest.mark.asyncio
@patch("app.core.marzban_client.MarzbanAPI")
async def test_get_stats(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_token = AsyncMock(return_value="test_token")
    mock_client.get_system_stats = AsyncMock(return_value={"cpu": 10})
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    assert await manager.get_stats() == {"cpu": 10}

@pytest.mark.asyncio
@patch("app.core.marzban_client.MarzbanAPI")
async def test_get_user(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_token = AsyncMock(return_value="test_token")
    mock_client.get_user = AsyncMock(return_value={"username": "test"})
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    assert await manager.get_user("test") == {"username": "test"}

@pytest.mark.asyncio
@patch("app.core.marzban_client.MarzbanAPI")
async def test_create_user(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_token = AsyncMock(return_value="test_token")
    mock_client.add_user = AsyncMock(return_value={"username": "new"})
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    await manager.create_user({"username": "new"})
    
    # Check that it was called with some object (UserCreate)
    args, kwargs = mock_client.add_user.call_args
    assert args[0].username == "new"

@pytest.mark.asyncio
@patch("app.core.marzban_client.MarzbanAPI")
async def test_modify_user(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_token = AsyncMock(return_value="test_token")
    mock_client.modify_user = AsyncMock(return_value={"username": "mod"})
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    await manager.modify_user("test_user", {"expire": 12345678})
    
    args, kwargs = mock_client.modify_user.call_args
    assert args[0] == "test_user"
    assert args[1].expire == 12345678

@pytest.mark.asyncio
@patch("app.core.marzban_client.MarzbanAPI")
async def test_token_refresh_on_401(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    
    # First call fails with 401, second succeeds
    error_401 = Exception("401 Unauthorized")
    error_401.response = MagicMock()
    error_401.response.status_code = 401
    
    mock_client.get_token = AsyncMock(return_value="new_token")
    mock_client.get_user = AsyncMock(side_effect=[error_401, {"username": "test"}])

    manager = MarzbanManager(config["address"], config["username"], config["password"])
    manager.token = "old_token"
    
    result = await manager.get_user("test")
    assert result == {"username": "test"}
    assert manager.token == "new_token"
    assert mock_client.get_token.call_count == 1
    assert mock_client.get_user.call_count == 2
