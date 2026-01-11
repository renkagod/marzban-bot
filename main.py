import asyncio
import logging
import os
from dotenv import load_dotenv

from app.bot.manager import BotManager
from app.core.database import DatabaseManager
from app.core.marzban_client import MarzbanManager
from app.core.monitor import HealthMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN")
    db_path = os.getenv("DATABASE_PATH", "bot.db")
    marzban_address = os.getenv("MARZBAN_ADDRESS")
    marzban_user = os.getenv("MARZBAN_USERNAME")
    marzban_pass = os.getenv("MARZBAN_PASSWORD")

    # Initialize Managers
    db = DatabaseManager(db_path)
    await db.connect()
    await db.create_tables()
    
    marzban = MarzbanManager(marzban_address, marzban_user, marzban_pass)
    
    bot_manager = BotManager(bot_token)
    
    # Initialize Health Monitor
    monitor = HealthMonitor(
        marzban, 
        bot_manager.bot, 
        os.getenv("ADMIN_CHANNEL_ID")
    )
    
    # Inject dependencies into DP if needed via dp.workflow_data
    bot_manager.dp["db"] = db
    bot_manager.dp["marzban"] = marzban

    try:
        # Start health monitor as background task
        monitor_task = asyncio.create_task(monitor.run())
        await bot_manager.start()
    finally:
        monitor.stop()
        await bot_manager.stop()
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
