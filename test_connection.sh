#!/bin/bash
source venv/bin/activate
export PYTHONPATH="."
python3 -c "import asyncio; from dotenv import load_dotenv; import os; from app.core.marzban_client import MarzbanManager; load_dotenv(); manager = MarzbanManager(os.getenv('MARZBAN_ADDRESS'), os.getenv('MARZBAN_USERNAME'), os.getenv('MARZBAN_PASSWORD')); print(f'Connection successful: {asyncio.run(manager.check_connectivity())}')"
