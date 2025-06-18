# api/zalo_api.py (File mới)
import zlapi
from config.config import settings
from api.base_client import BaseApiClient

class ZaloApiClient(BaseApiClient):
    def __init__(self):
        self.phone = settings.zalo.phone
        self.password = settings.zalo.password
        self.client = None
        self._login()

    def _login(self):
        try:
            print("Logging into Zalo...")
            self.client = zlapi.ZaloClient(self.phone, self.password)
            print("✅ Zalo login successful.")
        except Exception as e:
            print(f"❌ Zalo login failed: {e}")
            self.client = None
    
    def send_message(self, group_id: str, message: str):
        if not self.client: return
        try:
            self.client.send_text_message(group_id, message)
            print(f"Sent message to Zalo group {group_id}")
        except Exception as e:
            print(f"Failed to send Zalo message: {e}")

    def remove_user(self, group_id: str, user_id: str):
        if not self.client: return
        try:
            self.client.remove_members_from_group(group_id, [user_id])
            print(f"Removed user {user_id} from Zalo group {group_id}")
        except Exception as e:
            print(f"Failed to remove Zalo user: {e}")

# Tạo một instance duy nhất để toàn bộ ứng dụng sử dụng
zalo_api_client = ZaloApiClient()