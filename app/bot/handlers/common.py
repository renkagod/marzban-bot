from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, User
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
        referred_by = None
        if message.text and len(message.text.split()) > 1:
            ref_id = message.text.split()[1]
            if ref_id.isdigit():
                referred_by = int(ref_id)
        await db.add_user(message.from_user.id, message.from_user.username, referred_by=referred_by)
        user = await db.get_user(message.from_user.id)

    text = f"Привет, {message.from_user.full_name}!\n\nБаланс: {user['balance']} руб.\n\nВыберите действие:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подписка", callback_data="my_subscription")],
        [InlineKeyboardButton(text="Пригласить друзей", callback_data="referrals")],
        [InlineKeyboardButton(text="Поддержка", callback_data="support")]
    ])
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "referrals")
async def referral_menu(callback: CallbackQuery, db: DatabaseManager):
    user_id = callback.from_user.id
    count = await db.get_referral_count(user_id)
    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={user_id}"
    text = f"Реферальная программа\n\nПриглашайте друзей и получайте бонусы!\n\nВаша статистика:\nПриглашено: {count} чел.\n\nВаша ссылка:\n`{referral_link}`"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_main")]])
    await callback.message.edit_text(text, reply_markup=keyboard)

async def get_or_create_marzban_username(user_id: int, event_from_user: User, db: DatabaseManager) -> str:
    user = await db.get_user(user_id)
    if user and user.get('marzban_username'):
        return user['marzban_username']
    
    tg_name = event_from_user.username or event_from_user.first_name
    clean_name = "".join(c for c in tg_name.lower() if c.isalnum() or c == "_")
    marzban_username = f"{user_id}_{clean_name}"
    
    await db.update_marzban_username(user_id, marzban_username)
    return marzban_username

@router.callback_query(F.data == "my_subscription")
async def my_subscription_handler(callback: CallbackQuery, db: DatabaseManager, marzban: MarzbanManager):
    marzban_username = await get_or_create_marzban_username(callback.from_user.id, callback.from_user, db)
    
    try:
        m_user = await marzban.get_user(marzban_username)
        sub_prefix = os.getenv("SUB_URL_PREFIX", "").rstrip("/")
        
        # Robust handling of subscription URL
        full_sub_url = None
        if hasattr(m_user, 'subscription_url') and m_user.subscription_url:
            if sub_prefix and not m_user.subscription_url.startswith("http"):
                full_sub_url = f"{sub_prefix}{m_user.subscription_url}"
            else:
                full_sub_url = m_user.subscription_url
        
        # Format expire date
        expire_str = "Никогда"
        if hasattr(m_user, 'expire') and m_user.expire:
            try:
                expire_dt = datetime.fromtimestamp(m_user.expire)
                expire_str = expire_dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                expire_str = str(m_user.expire)
        
        # Format traffic
        used_gb = round(m_user.used_traffic / (1024**3), 2) if hasattr(m_user, 'used_traffic') else 0
        limit_gb = round(m_user.data_limit / (1024**3), 2) if hasattr(m_user, 'data_limit') and m_user.data_limit else "Безлимит"
        
        status_map = {
            "active": "✅ Активна",
            "expired": "❌ Истекла",
            "limited": "⚠️ Ограничена",
            "disabled": "🚫 Отключена",
            "on_hold": "⏳ В ожидании"
        }
        status_text = status_map.get(m_user.status, m_user.status) if hasattr(m_user, 'status') else "Неизвестно"

        text = (
            f"<b>Ваша подписка:</b>\n\n"
            f"👤 Логин: <code>{m_user.username}</code>\n"
            f"📊 Статус: {status_text}\n"
            f"💾 Трафик: {used_gb} ГБ / {limit_gb} ГБ\n"
            f"📅 Истекает: {expire_str}"
        )
        
        buttons = [[InlineKeyboardButton(text="Продлить подписку", callback_data="sub_plans:renew")]]
        
        if full_sub_url:
            buttons.append([InlineKeyboardButton(text="Открыть в браузере", url=full_sub_url)])
            buttons.append([
                InlineKeyboardButton(text="v2rayTun", url=f"v2raytun://import/{full_sub_url}"),
                InlineKeyboardButton(text="Streisand", url=f"streisand://import/{full_sub_url}")
            ])
            buttons.append([InlineKeyboardButton(text="Получить QR-код", callback_data=f"get_qr:{marzban_username}")])
        
        buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_main")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        if callback.message.photo:
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.message.delete()
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Error in my_subscription_handler for {marzban_username}: {e}", exc_info=True)
        await callback.message.edit_text(
            "У вас еще нет активной подписки или произошла ошибка при получении данных.\n\n"
            "Если вы только что оплатили подписку, подождите несколько секунд и попробуйте снова.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Купить подписку", callback_data="sub_plans:buy")],
                [InlineKeyboardButton(text="Обновить", callback_data="my_subscription")],
                [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
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
        [InlineKeyboardButton(text="Назад", callback_data="my_subscription")]
    ])
    title = "Продление подписки" if action == "renew" else "Покупка подписки"
    await callback.message.edit_text(f"<b>{title}</b>\n\nВыберите период:", reply_markup=keyboard)

async def process_subscription_action(user_id: int, action: str, days: int, marzban: MarzbanManager, event_from_user: User, db: DatabaseManager):
    marzban_username = await get_or_create_marzban_username(user_id, event_from_user, db)
    user_note = f"TG ID: {user_id}"
    if event_from_user.username: user_note += f" | @{event_from_user.username}"
    user_note += f" | {event_from_user.full_name}"
    user_exists = False
    try:
        await marzban.get_user(marzban_username)
        user_exists = True
    except Exception: user_exists = False
    
    if action == "buy" and not user_exists:
        limit_gb = int(os.getenv("DEFAULT_DATA_LIMIT_GB", "50"))
        data_limit = (limit_gb * 1024**3) if limit_gb > 0 else None
        
        # Ensure we at least enable vless and vmess as defaults if not specified
        user_data = {
            "username": marzban_username,
            "proxies": {"vless": {}, "vmess": {}}, 
            "expire": int((datetime.now() + timedelta(days=days)).timestamp()),
            "data_limit": data_limit,
            "note": user_note
        }
        await marzban.create_user(user_data)
    else:
        try:
            m_user = await marzban.get_user(marzban_username)
            # If user was expired, start from now. If not, add to existing expire.
            current_expire = m_user.expire if m_user.expire else int(datetime.now().timestamp())
            start_date = max(current_expire, int(datetime.now().timestamp()))
            await marzban.modify_user(marzban_username, {"expire": start_date + (days * 24 * 3600)})
        except Exception as e:
            logger.error(f"Failed to modify user {marzban_username}: {e}")
            raise e

@router.callback_query(F.data.startswith("checkout:"))
async def checkout_handler(callback: CallbackQuery, db: DatabaseManager, marzban: MarzbanManager, crypto: CryptoBotClient):
    _, action, days, price = callback.data.split(":")
    days, price, user_id = int(days), int(price), callback.from_user.id
    user = await db.get_user(user_id)
    if user['balance'] >= price:
        try:
            await process_subscription_action(user_id, action, days, marzban, callback.from_user, db)
            await db.update_balance(user_id, -float(price))
            await callback.answer("Успешно")
            await my_subscription_handler(callback, db, marzban)
        except Exception as e:
            logger.error(f"Subscription action failed: {e}"); await callback.message.answer("Ошибка при обработке")
    else:
        needed = price - user['balance']
        try:
            asset = os.getenv("PAYMENT_ASSET", "USDT")
            rates = await crypto.get_exchange_rates()
            rate_obj = next((r for r in rates if r['source'] == asset and r['target'] == 'RUB'), None)
            if not rate_obj: await callback.answer("Ошибка курса"); return
            rate, markup = float(rate_obj['rate']), float(os.getenv("PAYMENT_MARKUP_PERCENT", "0")) / 100
            amount_crypto = round((needed / rate) * (1 + markup), 2)
            payload = f"sub_auto:{action}:{days}:{price}"
            invoice = await crypto.create_invoice(amount=amount_crypto, asset=asset, description=f"Оплата подписки ({days} дн.)", payload=payload)
            pay_url = invoice.get('bot_invoice_url') or invoice.get('pay_url') or invoice.get('url')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=pay_url)], [InlineKeyboardButton(text="Проверить оплату", callback_data=f"check_pay:{invoice['invoice_id']}:{needed}")], [InlineKeyboardButton(text="Назад", callback_data="my_subscription")]])
            await callback.message.edit_text(f"Недостаточно средств. Необходимо доплатить {needed} руб. (~{amount_crypto} {asset})\n\nПосле оплаты подписка будет активирована автоматически.", reply_markup=keyboard)
            await db.add_payment(user_id, needed, "CryptoBot", str(invoice['invoice_id']))
        except Exception as e:
            logger.error(f"Error creating invoice: {e}"); await callback.answer("Ошибка счета")

@router.callback_query(F.data.startswith("check_pay:"))
async def check_payment_handler(callback: CallbackQuery, db: DatabaseManager, bot: Bot, crypto: CryptoBotClient, marzban: MarzbanManager):
    parts = callback.data.split(":")
    invoice_id = int(parts[1])
    try:
        invoices = await crypto.get_invoices(invoice_ids=[invoice_id])
        items = invoices.get("items", []) if isinstance(invoices, dict) else invoices
        invoice = next((inv for inv in items if int(inv['invoice_id']) == invoice_id), None)
        if invoice and invoice['status'] == "paid":
            db_p = await db.get_payment_by_external_id(str(invoice_id))
            if db_p and db_p['status'] == 'pending':
                await db.update_payment_status(db_p['id'], "completed")
                await db.update_balance(callback.from_user.id, db_p['amount'])
                payload = invoice.get('payload', '')
                if payload.startswith("sub_auto:"):
                    _, action, days, price = payload.split(":")
                    days, price = int(days), int(price)
                    user = await db.get_user(callback.from_user.id)
                    if user['balance'] >= price:
                        await process_subscription_action(callback.from_user.id, action, days, marzban, callback.from_user, db)
                        await db.update_balance(callback.from_user.id, -float(price))
                        await callback.message.answer("Оплата подтверждена, подписка активирована")
                    else: await callback.message.answer("Оплата подтверждена, баланс пополнен")
                else: await callback.message.edit_text("Оплата подтверждена")
                await bot.send_message(os.getenv("ADMIN_CHANNEL_ID"), f"Новая оплата\n\nПользователь: {callback.from_user.mention_html()}\nСумма: {db_p['amount']} руб.", message_thread_id=os.getenv("ADMIN_PAYMENTS_TOPIC_ID"))
                await my_subscription_handler(callback, db, marzban)
            else: await callback.answer("Уже обработано")
        else: await callback.answer("Оплата не найдена")
    except Exception as e:
        logger.error(f"Error checking payment: {e}"); await callback.answer("Ошибка проверки")

@router.callback_query(F.data.startswith("get_qr:"))
async def get_qr_handler(callback: CallbackQuery, db: DatabaseManager, marzban: MarzbanManager):
    marzban_username = callback.data.split(":")[1]
    try:
        m_user = await marzban.get_user(marzban_username)
        if hasattr(m_user, 'subscription_url') and m_user.subscription_url:
            await callback.message.answer_photo(photo=generate_qr_code(m_user.subscription_url), caption=f"Ваш QR-код (<code>{m_user.username}</code>)")
        else:
            await callback.answer("Ссылка для QR-кода еще не доступна", show_alert=True)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error generating QR: {e}"); await callback.answer("Ошибка")

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery, db: DatabaseManager):
    user = await db.get_user(callback.from_user.id)
    text = f"Привет, {callback.from_user.full_name}!\n\nБаланс: {user['balance']} руб.\n\nВыберите действие:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подписка", callback_data="my_subscription")], [InlineKeyboardButton(text="Пригласить друзей", callback_data="referrals")], [InlineKeyboardButton(text="Поддержка", callback_data="support")]])
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    support_user = os.getenv("SUPPORT_USERNAME", "@renkaa1")
    await callback.message.answer(f"Для связи с поддержкой напишите {support_user}")
    await callback.answer()

@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery, db: DatabaseManager):
    user_id, channel_id = callback.from_user.id, os.getenv("CHANNEL_ID")
    if not channel_id: await callback.answer("Ошибка конфигурации"); return
    try:
        member = await callback.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            await db.add_user(user_id, callback.from_user.username)
            await callback.answer("Подписка подтверждена")
            await callback.message.delete()
            user = await db.get_user(user_id)
            text = f"Привет, {callback.from_user.full_name}!\n\nБаланс: {user['balance']} руб.\n\nВыберите действие:"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подписка", callback_data="my_subscription")], [InlineKeyboardButton(text="Пригласить друзей", callback_data="referrals")], [InlineKeyboardButton(text="Поддержка", callback_data="support")]])
            await callback.message.answer(text, reply_markup=keyboard)
        else: await callback.answer("Вы не подписаны на канал")
    except Exception as e:
        logger.error(f"Error checking sub: {e}"); await callback.answer("Ошибка")