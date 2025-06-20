import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from telegram import Bot
from config import settings
from api.base_client import BaseApiClient

class TelegramApiClient(BaseApiClient):
    def __init__(self):
        self.bot = Bot(token=settings.telegram.token)

    async def send_message(self, group_id: str, message: str):
        try:
            await self.bot.send_message(chat_id=group_id, text=message)
            print(f"Sent message to Telegram group {group_id}")
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

    async def remove_user(self, group_id: str, user_id: str):
        try:
            # ban_chat_member vừa kick vừa cấm user quay lại, an toàn hơn
            await self.bot.ban_chat_member(chat_id=group_id, user_id=int(user_id))
            # Để chỉ kick mà không cấm, có thể unban ngay sau đó
            await self.bot.unban_chat_member(chat_id=group_id, user_id=int(user_id))
            print(f"Kicked user {user_id} from Telegram group {group_id}")
        except Exception as e:
            print(f"Failed to kick Telegram user: {e}")

# Tạo instance để dùng chung
telegram_api_client = TelegramApiClient()





# ==============================================================================
# KHỐI TEST
# ==============================================================================
if __name__ == "__main__":
    print("\n--- RUNNING DISCORD API CLIENT IN TEST MODE ---")
    if telegram_api_client.client:
        print("✅ Test run: Client initialized successfully.")
    else:
        print("❌ Test run: Client failed to initialize.")