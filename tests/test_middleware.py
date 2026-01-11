import pytest
from unittest.mock import AsyncMock, MagicMock
from app.bot.middlewares.error_handler import ErrorHandlerMiddleware

@pytest.mark.asyncio
async def test_error_handler_middleware_success():
    middleware = ErrorHandlerMiddleware()
    handler = AsyncMock(return_value="success")
    event = MagicMock()
    data = {}
    
    result = await middleware(handler, event, data)
    assert result == "success"
    handler.assert_called_once()

@pytest.mark.asyncio
async def test_error_handler_middleware_api_error():
    middleware = ErrorHandlerMiddleware()
    # Имитируем ошибку API
    handler = AsyncMock(side_effect=Exception("Marzban API error"))
    
    from aiogram.types import Message
    event = AsyncMock(spec=Message) # Use spec to pass isinstance check
    event.answer = AsyncMock()
    data = {}
    
    result = await middleware(handler, event, data)
    assert result is None
    event.answer.assert_called_with("Сервис временно недоступен. Попробуйте позже.")
