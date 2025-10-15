import asyncio
from typing import Optional
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

from .config import settings
from .db import insert_original


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Envie um link de vídeo ou anexe um vídeo. Ele entrará na fila como 'pending'.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    rec_id = insert_original(source_type="url", source_url=text, telegram_file_id=None, original_path=None)
    await update.message.reply_text(f"[BOT] recebido id={rec_id}")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    file = None
    if getattr(update.message, "video", None):
        file = update.message.video
    elif getattr(update.message, "document", None) and (getattr(update.message.document, "mime_type", "") or "").startswith("video/"):
        file = update.message.document
    if not file:
        return
    file_id = file.file_id
    rec_id = insert_original(source_type="telegram", source_url=None, telegram_file_id=file_id, original_path=None)
    await update.message.reply_text(f"[BOT] recebido id={rec_id}")


def run_bot_asyncio():
    import asyncio
    if not settings.TELEGRAM_BOT_TOKEN:
        print("[BOT] Token não configurado via env/app.config.")
        return
    
    # Criar novo event loop para esta thread
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler((filters.VIDEO | filters.Document.VIDEO), handle_video))
        
        print("[BOT] Iniciando bot do Telegram...")
        app.run_polling(close_loop=False)
    except Exception as e:
        print(f"[BOT] erro ao iniciar: {e}")
    finally:
        if loop:
            try:
                loop.close()
            except Exception:
                pass

