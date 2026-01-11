from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.database import DatabaseManager
from app.core.marzban_client import MarzbanManager
from app.core.cryptobot import CryptoBotClient
from app.utils.qr import generate_qr_code
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

def calculate_price(base_monthly: int, days: int) -> int:
    if days == 30:
        return base_monthly
    daily_base = base_monthly / 30
    if days == 14:
        return int(round((daily_base * 14) * 1.15))
    if days == 7:
        return int(round((daily_base * 7) * 1.30))
    return int(round(daily_base * days))

@router.message(Command("start"))
async def start_cmd(message: Message, db: DatabaseManager):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.username)
        user = await db.get_user(message.from_user.id)

    text = (
        f"Привет, {message.from_user.full_name}! 👋\n\n"
        f"💰 <b>Баланс:</b> {user['balance']} руб.\n\n"
        "Выберите действие:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Моя подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up")],
        [InlineKeyboardButton(text="👫 Рефералы", callback_data="referrals")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ])

    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "referrals")
async def referral_menu(callback: CallbackQuery, db: DatabaseManager):
    user_id = callback.from_user.id
    count = await db.get_referral_count(user_id)
    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    text = (
        f"<b>👫 Реферальная программа</b>\n\n"
        f"Приглашайте друзей и получайте бонусы!\n\n"
        f"📊 <b>Ваша статистика:</b>\n"
        f"👥 Приглашено: {count} чел.\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n`{referral_link}`"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "my_subscription")
async def my_subscription_handler(callback: CallbackQuery, db: DatabaseManager, marzban: MarzbanManager):
    marzban_username = f"user_{callback.from_user.id}"
    
    try:
        m_user = await marzban.get_user(marzban_username)
        status_emoji = "🟢" if m_user.status == "active" else "🔴"
        sub_prefix = os.getenv("SUB_URL_PREFIX", "").rstrip("/")
        full_sub_url = f"{sub_prefix}{m_user.subscription_url}" if sub_prefix else m_user.subscription_url

        text = (
            f"<b>💎 Ваша подписка:</b>\n\n"
            f"👤 <b>Логин:</b> `{m_user.username}`\n"
            f"📡 <b>Статус:</b> {status_emoji} {m_user.status}\n"
            f"📊 <b>Трафик:</b> {round(m_user.used_traffic / (1024**3), 2)} ГБ / "
            f"{round(m_user.data_limit / (1024**3), 2) if m_user.data_limit else '∞'} ГБ\n"
            f"📅 <b>Истекает:</b> {m_user.expire if m_user.expire else 'Никогда'}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="sub_plans:renew")],
            [InlineKeyboardButton(text="🔗 Открыть в браузере", url=full_sub_url)],
            [InlineKeyboardButton(text="🖼 Получить QR-код", callback_data=f"get_qr:{marzban_username}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception:
        await callback.message.edit_text(
            "У вас еще нет активной подписки.\nЖелаете приобрести?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍 Купить подписку", callback_data="sub_plans:buy")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ])
        )

@router.callback_query(F.data.startswith("sub_plans:"))
async def sub_plans_menu(callback: CallbackQuery, db: DatabaseManager):
    action = callback.data.split(":")[1]
    user = await db.get_user(callback.from_user.id)
    base_price = int(os.getenv("PRICE_INNER_CIRCLE", "149")) if user['group_name'] == "Inner Circle" else int(os.getenv("PRICE_STANDARD", "200"))
    
    p7, p14, p30 = calculate_price(base_price, 7), calculate_price(base_price, 14), base_price
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"7 дней — {p7} руб.", callback_data=f"checkout:{action}:7:{p7}")],
        [InlineKeyboardButton(text=f"14 дней — {p14} руб.", callback_data=f"checkout:{action}:14:{p14}")],
        [InlineKeyboardButton(text=f"30 дней — {p30} руб.", callback_data=f"checkout:{action}:30:{p30}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="my_subscription")]
    ])
    title = "Продление подписки" if action == "renew" else "Покупка подписки"
    await callback.message.edit_text(f"<b>{title}</b>\n\nВыберите период:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("checkout:"))
async def checkout_handler(callback: CallbackQuery, db: DatabaseManager, marzban: MarzbanManager):
    _, action, days, price = callback.data.split(":")
    days, price, user_id = int(days), int(price), callback.from_user.id
    marzban_username = f"user_{user_id}"
    
    user = await db.get_user(user_id)
    if user['balance'] < price:
        await callback.answer(f"Недостаточно средств. Нужно {price} руб., у вас {user['balance']} руб.", show_alert=True)
        return

    try:
        if action == "buy":
            user_data = {
                "username": marzban_username,
                "proxies": {}, # Let Marzban enable default protocols
                "expire": int((datetime.now() + timedelta(days=days)).timestamp()),
                "data_limit": 50 * 1024**3
            }
            await marzban.create_user(user_data)
        else:
            m_user = await marzban.get_user(marzban_username)
            current_expire = m_user.expire if m_user.expire else int(datetime.now().timestamp())
            start_date = max(current_expire, int(datetime.now().timestamp()))
            await marzban.modify_user(marzban_username, {"expire": start_date + (days * 24 * 3600)})

        await db.update_balance(user_id, -float(price))
        await callback.answer("✅ Успешно! Подписка активирована/продлена.", show_alert=True)
        await my_subscription_handler(callback, db, marzban)
    except Exception as e:
        logger.error(f"Subscription action failed: {e}")
        await callback.answer("Ошибка при обработке подписки.", show_alert=True)

@router.callback_query(F.data == "top_up")
async def top_up_menu(callback: CallbackQuery, db: DatabaseManager):
    user = await db.get_user(callback.from_user.id)
    price_standard, price_inner = int(os.getenv("PRICE_STANDARD", "200")), int(os.getenv("PRICE_INNER_CIRCLE", "149"))
    primary_price = price_inner if user['group_name'] == "Inner Circle" else price_standard
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{primary_price} руб.", callback_data=f"buy:{primary_price}")],
        [InlineKeyboardButton(text="500 руб.", callback_data="buy:500")],
        [InlineKeyboardButton(text="1000 руб.", callback_data="buy:1000")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(f"<b>💳 Пополнение баланса</b>\n\nСумма к оплате: <b>{primary_price} руб.</b>\n\nВыберите сумму:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("buy:"))
async def create_invoice_handler(callback: CallbackQuery, db: DatabaseManager, crypto: CryptoBotClient):
    amount_rub = float(callback.data.split(":")[1])
    try:
        rates = await crypto.get_exchange_rates()
        usdt_rub_rate = next((float(r['rate']) for r in rates if r['source'] == 'USDT' and r['target'] == 'RUB'), None)
        if not usdt_rub_rate:
            await callback.answer("Не удалось получить курс валют.", show_alert=True)
            return

        markup = float(os.getenv("PAYMENT_MARKUP_PERCENT", "0")) / 100
        amount_usdt = round((amount_rub / usdt_rub_rate) * (1 + markup), 2)
        invoice = await crypto.create_invoice(amount=amount_usdt, asset="USDT", description=f"Пополнение на {amount_rub} руб.", payload=str(callback.from_user.id))
        
        # Use bot_invoice_url instead of pay_url
        pay_url = invoice.get('bot_invoice_url') or invoice.get('pay_url') or invoice.get('url')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=pay_url)],
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_pay:{invoice['invoice_id']}:{amount_rub}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="top_up")]
        ])
        await callback.message.edit_text(f"Счет на {amount_rub} руб. (~{amount_usdt} USDT) создан!\n\nКурс: {usdt_rub_rate} руб/USDT (наценка {os.getenv('PAYMENT_MARKUP_PERCENT', '0')}%).", reply_markup=keyboard)
        await db.add_payment(callback.from_user.id, amount_rub, "CryptoBot", str(invoice['invoice_id']))
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        await callback.answer("Ошибка при создании счета.", show_alert=True)

@router.callback_query(F.data.startswith("check_pay:"))
async def check_payment_handler(callback: CallbackQuery, db: DatabaseManager, bot: Bot, crypto: CryptoBotClient):
    parts = callback.data.split(":")
    invoice_id, amount_rub = int(parts[1]), float(parts[2]) if len(parts) > 2 else 0.0
    try:
        invoices = await crypto.get_invoices(invoice_ids=[invoice_id])
        items = invoices.get("items", []) if isinstance(invoices, dict) else invoices
        invoice = next((inv for inv in items if int(inv['invoice_id']) == invoice_id), None)
        
        if invoice and invoice['status'] == "paid":
            db_p = await db.get_payment_by_external_id(str(invoice_id))
            if db_p and db_p['status'] == 'pending':
                credit = db_p['amount'] if db_p['amount'] > 0 else amount_rub
                await db.update_payment_status(db_p['id'], "completed")
                await db.update_balance(callback.from_user.id, credit)
                await callback.message.edit_text(f"✅ Оплата подтверждена! Баланс пополнен на {credit} руб.")
                await bot.send_message(os.getenv("ADMIN_CHANNEL_ID"), f"💰 <b>Новая оплата!</b>\n\n👤 {callback.from_user.mention_html()}\n🆔 <code>{callback.from_user.id}</code>\n💵 {credit} руб.", message_thread_id=os.getenv("ADMIN_PAYMENTS_TOPIC_ID"))
            else:
                await callback.answer("Баланс уже пополнен.", show_alert=True)
        else:
            await callback.answer("Оплата пока не поступила.", show_alert=True)
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        await callback.answer("Ошибка при проверке оплаты.")

@router.callback_query(F.data.startswith("get_qr:"))
async def get_qr_handler(callback: CallbackQuery, marzban: MarzbanManager):
    user_name = callback.data.split(":")[1]
    try:
        m_user = await marzban.get_user(user_name)
        await callback.message.answer_photo(photo=generate_qr_code(m_user.subscription_url), caption=f"Ваш QR-код (<code>{m_user.username}</code>)")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error generating QR: {e}"); await callback.answer("Ошибка генерации QR.")

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, db: DatabaseManager):
    user = await db.get_user(callback.from_user.id)
    text = f"Привет, {callback.from_user.full_name}! 👋\n\n💰 <b>Баланс:</b> {user['balance']} руб.\n\nВыберите действие:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💎 Моя подписка", callback_data="my_subscription")], [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up")], [InlineKeyboardButton(text="👫 Рефералы", callback_data="referrals")], [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]])
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    await callback.answer("Для связи с поддержкой напишите @renkaa1", show_alert=True)

@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery, db: DatabaseManager):
    user_id, channel_id = callback.from_user.id, os.getenv("CHANNEL_ID")
    if not channel_id: await callback.answer("Ошибка конфигурации."); return
    try:
        member = await callback.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            await db.add_user(user_id, callback.from_user.username)
            await callback.answer("Подписка подтверждена! 🎉", show_alert=True)
            await callback.message.delete()
        else:
            await callback.answer("Вы все еще не подписаны на канал!", show_alert=True)
    except Exception as e:
        logger.error(f"Error checking sub: {e}"); await callback.answer("Ошибка проверки.")