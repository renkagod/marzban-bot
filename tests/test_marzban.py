import pytest
from unittest.mock import MagicMock, patch
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
        address=config["address"],
        username=config["username"],
        password=config["password"]
    )

@patch("app.core.marzban_client.MarzbanAPI")
def test_marzban_connectivity_success(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_system_stats.return_value = {"status": "running"}
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    assert manager.check_connectivity() is True
    mock_client.get_system_stats.assert_called_once()

@patch("app.core.marzban_client.MarzbanAPI")
def test_marzban_connectivity_failure(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_system_stats.side_effect = Exception("Connection error")
    
    manager = MarzbanManager(config["address"], config["username"], config["password"])
    assert manager.check_connectivity() is False

@patch("app.core.marzban_client.MarzbanAPI")
def test_get_stats(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_system_stats.return_value = {"cpu": 10}
    
    manager = MarzbanManager(config["address"])
    assert manager.get_stats() == {"cpu": 10}

@patch("app.core.marzban_client.MarzbanAPI")
def test_get_user(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.get_user.return_value = {"username": "test"}
    
    manager = MarzbanManager(config["address"])
    assert manager.get_user("test") == {"username": "test"}

@patch("app.core.marzban_client.MarzbanAPI")
def test_create_user(mock_marzban, config):
    mock_client = MagicMock()
    mock_marzban.return_value = mock_client
    mock_client.add_user.return_value = {"username": "new"}
    
    manager = MarzbanManager(config["address"])
    assert manager.create_user({"username": "new"}) == {"username": "new"}