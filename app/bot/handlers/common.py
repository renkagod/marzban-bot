from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.core.database import DatabaseManager
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.database import DatabaseManager
from app.core.marzban_client import MarzbanManager
from app.core.cryptobot import CryptoBotClient
from app.utils.qr import generate_qr_code
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "top_up")
async def top_up_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="150 руб.", callback_data="buy:150")],
        [InlineKeyboardButton(text="200 руб.", callback_data="buy:200")],
        [InlineKeyboardButton(text="500 руб.", callback_data="buy:500")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("Выберите сумму пополнения:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("buy:"))
async def create_invoice_handler(callback: CallbackQuery, db: DatabaseManager):
    amount_rub = float(callback.data.split(":")[1])
    
    # Initialize CryptoBot (get from DP or env)
    # For now, we'll assume it's in DP or we'll use a factory
    # In main.py we'll add it to DP
    crypto: CryptoBotClient = callback.bot.dp.workflow_data.get("crypto")
    if not crypto:
        # Fallback for manual testing or if not in DP yet
        crypto = CryptoBotClient(os.getenv("CRYPTOBOT_TOKEN"), testnet=os.getenv("CRYPTOBOT_TESTNET", "False").lower() == "true")

    try:
        # Convert RUB to USDT or other asset if needed
        # For simplicity, we'll just pass the amount as is if the user wants USDT = RUB (unlikely)
        # Usually we need a converter. Let's assume we use USDT and fix rate for now
        # OR better: CryptoBot supports fiat currency in createInvoice
        
        invoice = await crypto.create_invoice(
            amount=amount_rub, 
            asset="USDT", # Or dynamic
            description=f"Пополнение баланса на {amount_rub} руб.",
            payload=str(callback.from_user.id)
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=invoice['pay_url'])],
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_pay:{invoice['invoice_id']}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="top_up")]
        ])
        
        await callback.message.edit_text(
            f"Счет на {amount_rub} руб. создан!\n\n"
            "После оплаты нажмите кнопку 'Проверить оплату'.",
            reply_markup=keyboard
        )
        
        # Log pending payment in DB
        await db.add_payment(
            telegram_id=callback.from_user.id,
            amount=amount_rub,
            provider="CryptoBot",
            external_id=str(invoice['invoice_id'])
        )
        
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        await callback.answer("Ошибка при создании счета. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data.startswith("check_pay:"))
async def check_payment_handler(callback: CallbackQuery, db: DatabaseManager, bot: Bot):
    invoice_id = int(callback.data.split(":")[1])
    crypto: CryptoBotClient = callback.bot.dp.workflow_data.get("crypto")
    if not crypto:
        crypto = CryptoBotClient(os.getenv("CRYPTOBOT_TOKEN"), testnet=os.getenv("CRYPTOBOT_TESTNET", "False").lower() == "true")

    try:
        invoices = await crypto.get_invoices(invoice_ids=[invoice_id])
        # get_invoices returns a list or dict with items
        items = invoices.get("items", []) if isinstance(invoices, dict) else invoices
        
        invoice = next((inv for inv in items if int(inv['invoice_id']) == invoice_id), None)
        
        if invoice and invoice['status'] == "paid":
            # Update payment in DB
            db_payment = await db.get_payment_by_external_id(str(invoice_id))
            if db_payment and db_payment['status'] == 'pending':
                await db.update_payment_status(db_payment['id'], "completed")
                await db.update_balance(callback.from_user.id, float(invoice['amount']))
                
                await callback.message.edit_text(
                    f"✅ Оплата подтверждена! Ваш баланс пополнен на {invoice['amount']} руб."
                )
                
                # Notify Admin
                admin_channel_id = os.getenv("ADMIN_CHANNEL_ID")
                admin_topic_id = os.getenv("ADMIN_PAYMENTS_TOPIC_ID")
                await bot.send_message(
                    chat_id=admin_channel_id,
                    text=f"💰 Новая оплата!\nПользователь: {callback.from_user.full_name} ({callback.from_user.id})\nСумма: {invoice['amount']} руб.",
                    message_thread_id=admin_topic_id if admin_topic_id else None
                )
            else:
                await callback.answer("Баланс уже был пополнен.", show_alert=True)
        else:
            await callback.answer("Оплата пока не поступила. Попробуйте через минуту.", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        await callback.answer("Ошибка при проверке оплаты.")

@router.callback_query(F.data.startswith("get_qr:"))
async def get_qr_handler(callback: CallbackQuery, marzban: MarzbanManager):
    marzban_username = callback.data.split(":")[1]
    
    try:
        m_user = await marzban.get_user(marzban_username)
        qr_file = generate_qr_code(m_user.subscription_url)
        
        await callback.message.answer_photo(
            photo=qr_file,
            caption=f"Ваш QR-код для подключения (<code>{m_user.username}</code>)"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error generating QR: {e}")
        await callback.answer("Ошибка при генерации QR-кода.", show_alert=True)

@router.message(Command("start"))
async def start_cmd(message: Message, db: DatabaseManager):
    user = await db.get_user(message.from_user.id)
    if not user:
        # Should be handled by middleware, but just in case
        await db.add_user(message.from_user.id, message.from_user.username)
        user = await db.get_user(message.from_user.id)

    text = (
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        f"💰 <b>Баланс:</b> {user['balance']} руб.\n"
        f"👥 <b>Группа:</b> {user['group_name']}\n\n"
        "Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Моя подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "my_subscription")
async def my_subscription_handler(callback: CallbackQuery, db: DatabaseManager, marzban: MarzbanManager):
    user = await db.get_user(callback.from_user.id)
    
    # In Marzban, user usually has a username. We can use telegram ID as username if we created them that way.
    # For now, let's try to get user by telegram ID (as string) or username.
    # Usually, we'll name the Marzban user like 'user_12345678'
    marzban_username = f"user_{callback.from_user.id}"
    
    try:
        m_user = await marzban.get_user(marzban_username)
        
        status_emoji = "🟢" if m_user.status == "active" else "🔴"
        
        text = (
            f"<b>Ваша подписка:</b>\n\n"
            f"👤 <b>Логин:</b> <code>{m_user.username}</code>\n"
            f"📡 <b>Статус:</b> {status_emoji} {m_user.status}\n"
            f"📊 <b>Трафик:</b> {round(m_user.used_traffic / (1024**3), 2)} ГБ / "
            f"{round(m_user.data_limit / (1024**3), 2) if m_user.data_limit else '∞'} ГБ\n"
            f"📅 <b>Истекает:</b> {m_user.expire if m_user.expire else 'Никогда'}\n\n"
            f"🔗 <b>Ссылка:</b> <code>{m_user.subscription_url}</code>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🖼 Получить QR-код", callback_data=f"get_qr:{marzban_username}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        await callback.answer("Подписка не найдена. Пополните баланс для активации.", show_alert=True)

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, db: DatabaseManager):
    user = await db.get_user(callback.from_user.id)
    
    text = (
        f"Привет, {callback.from_user.full_name}! 👋\n\n"
        f"💰 <b>Баланс:</b> {user['balance']} руб.\n"
        f"👥 <b>Группа:</b> {user['group_name']}\n\n"
        "Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Моя подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    await callback.answer("Для связи с поддержкой напишите @renkaa1", show_alert=True)

@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery, db: DatabaseManager):
    user_id = callback.from_user.id
    channel_id = os.getenv("CHANNEL_ID")
    
    if not channel_id:
        await callback.answer("Ошибка конфигурации: CHANNEL_ID не задан.")
        return

    try:
        member = await callback.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            # Register user in DB
            await db.add_user(user_id, callback.from_user.username)
            await callback.answer("Подписка подтверждена! 🎉", show_alert=True)
            await callback.message.delete()
            # Optionally send /start message again or main menu
        else:
            await callback.answer("Вы все еще не подписаны на канал!", show_alert=True)
    except Exception as e:
        logger.error(f"Error checking subscription in handler: {e}")
        await callback.answer("Произошла ошибка при проверке. Попробуйте позже.")
