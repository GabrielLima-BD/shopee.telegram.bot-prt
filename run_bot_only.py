# Runner para iniciar apenas o bot do Telegram sem GUI
# Use: python run_bot_only.py

from app import bot_ingest

if __name__ == '__main__':
    bot_ingest.run_bot_asyncio()
