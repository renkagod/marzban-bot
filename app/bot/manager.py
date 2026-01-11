from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.bot.middlewares.error_handler import ErrorHandlerMiddleware
from app.bot.handlers import admin
import logging

class BotManager:
    def __init__(self, token: str):
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher()
        self._setup_routers()
        self._setup_middlewares()

    def _setup_routers(self):
        self.dp.include_router(admin.router)

    def _setup_middlewares(self):
        self.dp.message.middleware(ErrorHandlerMiddleware())
        self.dp.callback_query.middleware(ErrorHandlerMiddleware())

    async def start(self):
        logging.info("Starting bot...")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        logging.info("Stopping bot...")
        await self.bot.session.close()
