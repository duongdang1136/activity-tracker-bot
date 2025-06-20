import sys
import os
    # Lấy đường dẫn của thư mục cha (tức là thư mục gốc của dự án)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # Thêm thư mục gốc vào sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from zlapi import ZaloAPI, MessageObject, EventObject, ThreadType
from zlapi.models import *
from config import settings
from api.base_client import BaseApiClient
from typing import Dict
from datetime import datetime, timedelta
from typing import Optional
from munch import Munch

class ZaloApiClient(BaseApiClient):
    def __init__(self):
        self.phone = settings.zalo.phone
        self.password = settings.zalo.password
        self.imei = settings.zalo.imei
        self.cookies = settings.zalo.cookies
        self.client: ZaloAPI | None = None
        self._login()

    def _login(self):
        try:
            print("Logging into Zalo...")
            self.client = ZaloAPI(self.phone, self.password, self.imei, self.cookies)
            my_info = self.client.fetchAccountInfo().profile.get("userId")
            print("✅ Zalo login successful.")
        except Exception as e:
            print(f"❌ Zalo login failed: {e}")
            self.client = None
    
    def send_message(self, group_id: str, message: str):
        if not self.client: 
            print("❌ Zalo client not initialized. Cannot send message.")
            return
        try:
            self.client.send_text_message(group_id, message)
            print(f"Sent message to Zalo group {group_id}")
        except Exception as e:
            print(f"Failed to send Zalo message: {e}")

    def remove_user(self, group_id: str, user_id: str):
        if not self.client:
            print("❌ Zalo client not initialized. Cannot remove user.")
            return
        try:
            self.client.remove_members_from_group(group_id, [user_id])
            print(f"Removed user {user_id} from Zalo group {group_id}")
        except Exception as e:
            print(f"Failed to remove Zalo user: {e}")

    def get_user_info(self, user_id: str):
        if not self.client: return None
        try:
            return self.client.get_user_info(user_id)
        except Exception as e:
            print(f"Could not get info for Zalo user {user_id}: {e}")
            return None

# Tạo một instance duy nhất để toàn bộ ứng dụng sử dụng
zalo_api_client = ZaloApiClient()




# KHỐI TEST (có thể giữ lại để kiểm tra độc lập)
# ==============================================================================
if __name__ == "__main__":
    # Thêm lại sys.path chỉ trong khối test này
    print("\n--- RUNNING ZALO API CLIENT IN TEST MODE ---")
    if zalo_api_client.client:
        print("✅ Test run: Client initialized successfully.")
    else:
        print("❌ Test run: Client failed to initialize.")