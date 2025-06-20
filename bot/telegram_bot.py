# bot/telegram_bot.py
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from services.activity_service import ActivityService
from config import settings

# --- Hàm xử lý sự kiện ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat = update.message.chat

    # Chỉ xử lý tin nhắn trong group, bỏ qua tin nhắn riêng
    if chat.type == 'private':
        return

    ActivityService.track_message(
        platform_name="Telegram",
        user_id=str(user.id),
        user_name=user.full_name,
        group_id=str(chat.id),
        group_name=chat.title
    )

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat = update.message.chat
    if chat.type == 'private':
        return
    
    ActivityService.track_sticker(
        platform_name="Telegram",
        user_id=str(user.id),
        user_name=user.full_name,
        group_id=str(chat.id),
        group_name=chat.title
    )
    
# Hàm để chạy bot, được gọi từ main.py
async def start_telegram_bot():
    print("🤖 Telegram Bot is starting...")
    application = ApplicationBuilder().token(settings.telegram.token).build()

    # Đăng ký các handler
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    sticker_handler = MessageHandler(filters.Sticker.ALL, handle_sticker)
    
    application.add_handler(message_handler)
    application.add_handler(sticker_handler)

    try:
        await application.initialize()
        await application.start()
        print("✅ Telegram Bot is running.")
        await application.updater.start_polling()
        # Giữ bot chạy
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        print(f"❌ An error occurred in Telegram bot: {e}")