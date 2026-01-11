from fastapi import FastAPI, Request, HTTPException
from app.core.database import DatabaseManager
from app.core.marzban_client import MarzbanManager
from app.core.freekassa import FreeKassaClient
from aiogram import Bot
import logging
import os

logger = logging.getLogger(__name__)

def create_webhook_app(db: DatabaseManager, marzban: MarzbanManager, freekassa: FreeKassaClient, bot: Bot):
    app = FastAPI()

    @app.post("/freekassa/webhook")
    async def freekassa_webhook(request: Request):
        # FK sends data as form-data usually
        data = await request.form()
        data_dict = dict(data)
        
        logger.info(f"Received FreeKassa webhook: {data_dict}")
        
        if not freekassa.verify_notification(data_dict):
            logger.warning("Invalid FreeKassa signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
            
        # o is merchant_order_id (e.g., FK_123_456)
        order_id = data_dict.get('o')
        amount = float(data_dict.get('oa'))
        
        db_p = await db.get_payment_by_external_id(order_id)
        if db_p and db_p['status'] == 'pending':
            user_id = db_p['telegram_id']
            await db.update_payment_status(db_p['id'], "completed")
            await db.update_balance(user_id, amount)
            
            # Try to notify user
            try:
                await bot.send_message(user_id, f"Оплата через FreeKassa на сумму {amount} руб. принята! Баланс пополнен.")
                # We don't have the subscription context (days, price) here easily 
                # unless we store it in the database or parse from order_id.
                # For now, just topping up balance is safe.
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
                
            # Notify admin
            try:
                admin_channel = os.getenv("ADMIN_CHANNEL_ID")
                if admin_channel:
                    await bot.send_message(admin_channel, f"Новая оплата (FreeKassa)\nПользователь ID: {user_id}\nСумма: {amount} руб.")
            except Exception: pass
            
            return "YES"
        
        return "OK"

    return app
