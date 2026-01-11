import asyncio
import logging
from app.core.marzban_client import MarzbanManager
from aiogram import Bot
import os

logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, marzban: MarzbanManager, bot: Bot, admin_channel_id: str, interval: int = 60):
        self.marzban = marzban
        self.bot = bot
        self.admin_channel_id = admin_channel_id
        self.interval = interval
        self.is_running = False
        self.last_status = True # True for OK, False for Down

    async def check(self):
        status = await self.marzban.check_connectivity()
        
        if status != self.last_status:
            if not status:
                await self.send_alert("⚠️ ВНИМАНИЕ: Marzban API недоступен!")
            else:
                await self.send_alert("✅ Marzban API снова в строю.")
            self.last_status = status

    async def send_alert(self, text: str):
        try:
            # For now, we use ADMIN_CHANNEL_ID from env
            # You can also specify a topic ID if using forum channels
            topic_id = os.getenv("ADMIN_MONITOR_TOPIC_ID")
            await self.bot.send_message(
                chat_id=self.admin_channel_id,
                text=text,
                message_thread_id=topic_id if topic_id else None
            )
        except Exception as e:
            logger.error(f"Failed to send health alert: {e}")

    async def run(self):
        self.is_running = True
        logger.info(f"Health monitor started (interval: {self.interval}s)")
        while self.is_running:
            await self.check()
            await asyncio.sleep(self.interval)

    def stop(self):
        self.is_running = False
