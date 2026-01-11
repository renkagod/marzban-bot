import aiosqlite
import os

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row

    async def disconnect(self):
        if self.conn:
            await self.conn.close()

    async def create_tables(self):
        async with self.conn.cursor() as cursor:
            # Users table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    marzban_username TEXT,
                    group_name TEXT DEFAULT 'Standard',
                    balance REAL DEFAULT 0.0,
                    referred_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Check if marzban_username column exists (for migrations)
            try:
                await cursor.execute("ALTER TABLE users ADD COLUMN marzban_username TEXT")
            except Exception:
                pass # Column already exists

            # Payments table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    amount REAL,
                    provider TEXT,
                    external_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Referral rewards table
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referee_id INTEGER,
                    reward_amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await self.conn.commit()

    async def add_user(self, telegram_id: int, username: str = None, referred_by: int = None):
        async with self.conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, referred_by) VALUES (?, ?, ?)",
            (telegram_id, username, referred_by)
        ) as cursor:
            await self.conn.commit()

    async def update_marzban_username(self, telegram_id: int, marzban_username: str):
        await self.conn.execute(
            "UPDATE users SET marzban_username = ? WHERE telegram_id = ?",
            (marzban_username, telegram_id)
        )
        await self.conn.commit()

    async def get_user(self, telegram_id: int):
        async with self.conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_user_group(self, telegram_id: int, group_name: str):
        await self.conn.execute(
            "UPDATE users SET group_name = ? WHERE telegram_id = ?",
            (group_name, telegram_id)
        )
        await self.conn.commit()

    async def update_balance(self, telegram_id: int, amount: float):
        await self.conn.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
            (amount, telegram_id)
        )
        await self.conn.commit()

    async def get_referral_count(self, telegram_id: int) -> int:
        async with self.conn.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_all_users(self):
        async with self.conn.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_users_by_group(self, group_name: str):
        async with self.conn.execute(
            "SELECT * FROM users WHERE group_name = ?",
            (group_name,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_payment(self, telegram_id: int, amount: float, provider: str, external_id: str):
        async with self.conn.execute(
            "INSERT INTO payments (telegram_id, amount, provider, external_id) VALUES (?, ?, ?, ?)",
            (telegram_id, amount, provider, external_id)
        ) as cursor:
            payment_id = cursor.lastrowid
            await self.conn.commit()
            return payment_id

    async def get_payment(self, payment_id: int):
        async with self.conn.execute(
            "SELECT * FROM payments WHERE id = ?",
            (payment_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_payment_by_external_id(self, external_id: str):
        async with self.conn.execute(
            "SELECT * FROM payments WHERE external_id = ?",
            (external_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_payment_status(self, payment_id: int, status: str):
        await self.conn.execute(
            "UPDATE payments SET status = ? WHERE id = ?",
            (status, payment_id)
        )
        await self.conn.commit()
