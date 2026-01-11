#!/bin/bash
# Переходим в папку бота
cd /opt/marzban_bot

# Устанавливаем локальный адрес в .env бота
sed -i 's|^MARZBAN_ADDRESS=.*|MARZBAN_ADDRESS=http://127.0.0.1:8000|' .env

echo "Updated MARZBAN_ADDRESS to http://127.0.0.1:8000 in /opt/marzban_bot/.env"

# Запускаем тест связи
source venv/bin/activate
export PYTHONPATH="."
python3 -c "import asyncio; from dotenv import load_dotenv; import os; from app.core.marzban_client import MarzbanManager; load_dotenv(); manager = MarzbanManager(os.getenv('MARZBAN_ADDRESS'), os.getenv('MARZBAN_USERNAME'), os.getenv('MARZBAN_PASSWORD')); print(f'Connection successful: {asyncio.run(manager.check_connectivity())}')"
