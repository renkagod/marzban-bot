from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error handling event {event}: {e}", exc_info=True)
            
            # Сообщаем пользователю об ошибке в зависимости от типа события
            error_text = "Сервис временно недоступен. Попробуйте позже."
            
            if isinstance(event, Message):
                await event.answer(error_text)
            elif isinstance(event, CallbackQuery):
                await event.answer(error_text, show_alert=True)
            
            return None
