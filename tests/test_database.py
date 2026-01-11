import pytest
import os
import aiosqlite
from app.core.database import DatabaseManager

@pytest.fixture
async def db():
    test_db = "test_bot.db"
    manager = DatabaseManager(test_db)
    await manager.connect()
    await manager.create_tables()
    yield manager
    await manager.disconnect()
    if os.path.exists(test_db):
        os.remove(test_db)

@pytest.mark.asyncio
async def test_user_creation_retrieval(db):
    user_id = 123456789
    username = "testuser"
    await db.add_user(user_id, username)
    user = await db.get_user(user_id)
    assert user is not None
    assert user['telegram_id'] == user_id
    assert user['username'] == username
    assert user['group_name'] == "Standard"
    assert user['balance'] == 0.0

@pytest.mark.asyncio
async def test_user_group_update(db):
    user_id = 123456789
    await db.add_user(user_id, "testuser")
    await db.update_user_group(user_id, "Inner Circle")
    user = await db.get_user(user_id)
    assert user['group_name'] == "Inner Circle"

@pytest.mark.asyncio
async def test_balance_update(db):
    user_id = 123456789
    await db.add_user(user_id, "testuser")
    await db.update_balance(user_id, 500.0)
    user = await db.get_user(user_id)
    assert user['balance'] == 500.0

@pytest.mark.asyncio
async def test_list_users(db):
    await db.add_user(1, "user1")
    await db.add_user(2, "user2")
    users = await db.get_all_users()
    assert len(users) >= 2

@pytest.mark.asyncio
async def test_get_users_by_group(db):
    await db.add_user(1, "user1")
    await db.add_user(2, "user2")
    await db.update_user_group(1, "Inner Circle")
    inner_circle = await db.get_users_by_group("Inner Circle")
    assert len(inner_circle) == 1
    assert inner_circle[0]['telegram_id'] == 1

@pytest.mark.asyncio
async def test_payment_recording(db):
    user_id = 123456789
    await db.add_user(user_id, "testuser")
    payment_id = await db.add_payment(user_id, 150.0, "CryptoBot", "ext_123")
    assert payment_id is not None
    payment = await db.get_payment(payment_id)
    assert payment['status'] == "pending"
    await db.update_payment_status(payment_id, "completed")
    payment = await db.get_payment(payment_id)
    assert payment['status'] == "completed"
