from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.database import DatabaseManager
import logging
import os

logger = logging.getLogger(__name__)

class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        db: DatabaseManager = data.get("db")
        user_id = event.from_user.id
        
        # Check if user is already registered in DB
        user = await db.get_user(user_id)
        if user:
            return await handler(event, data)

        # For new users, check channel subscription
        try:
            member = await event.bot.get_chat_member(chat_id=self.channel_id, user_id=user_id)
            if member.status in ["member", "administrator", "creator"]:
                # Capture referrer if present in /start command
                referred_by = None
                if event.text and event.text.startswith("/start "):
                    parts = event.text.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        referred_by = int(parts[1])
                        if referred_by == user_id: # Prevent self-referral
                            referred_by = None

                # Register user in DB upon successful subscription check
                await db.add_user(user_id, event.from_user.username, referred_by=referred_by)
                return await handler(event, data)
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")

        # Use URL from env or fallback to username formatting
        channel_url = os.getenv("CHANNEL_URL")
        if not channel_url:
            channel_url = f"https://t.me/{self.channel_id.replace('@', '')}"

        # If not subscribed or error, prompt to subscribe
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подписаться на канал", url=channel_url)],
            [InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")]
        ])
        
        await event.answer(
            "Для использования бота необходимо подписаться на наш канал!",
            reply_markup=keyboard
        )
        return None
