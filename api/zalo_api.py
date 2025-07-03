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
        """
        Xử lý logic đăng nhập và kiểm tra trạng thái client một cách đáng tin cậy.
        """
        try:
            print("Logging into Zalo...")
            # Khởi tạo client
            client_instance = ZaloAPI(self.phone, self.password, self.imei, self.cookies)

            self.client = client_instance
            print("✅ Zalo client initialized successfully. Ready to listen and send messages.")           
            """
            # ==================================================================
            # KHỐI DEBUG - IN RA TẤT CẢ CÁC PHƯƠNG THỨC CỦA ĐỐI TƯỢNG CLIENT
            # ==================================================================
            print("\n--- DEBUG: Inspecting a ZaloAPI instance ---")
            # dir() là một hàm của Python để liệt kê tất cả các thuộc tính và phương thức của một đối tượng
            all_attributes = dir(self.client)
            
            # Lọc ra những phương thức mà chúng ta quan tâm (không bắt đầu bằng '_')
            public_methods = [attr for attr in all_attributes if not attr.startswith('_') and callable(getattr(self.client, attr))]
            
            print("Available public methods found:")
            for method_name in public_methods:
                print(f"  - {method_name}")
            print("--- END DEBUG ---\n")
            # ==================================================================
            """
        except Exception as e:
            print(f"❌ Zalo login failed with exception: {e}")
            self.client = None

    def get_user_info(self, user_id: str):
        if not self.client: return None
        try:
            return self.client.fetchUserInfo(self.phone)
        except Exception as e:
            print(f"Could not get info for Zalo user {user_id}: {e}")
            return None
        

            
    def send_message(self, message: str, user_id: str = None, group_id: str = None):
        """
        Gửi một tin nhắn văn bản đến người dùng hoặc một nhóm.
        Sử dụng tên phương thức và tham số chính xác đã được xác định qua debug.

        Args:
            message (str): Nội dung tin nhắn.
            user_id (str, optional): ID của người dùng (SĐT).
            group_id (str, optional): ID của nhóm.

        Raises:
            Exception: Ném lại exception nếu việc gửi tin nhắn thất bại.
        """
        if not self.client:
            print("❌ Zalo client not initialized.")
            raise ConnectionError("Zalo client is not connected.")
        
        thread_id = None
        thread_type = None

        # Ưu tiên gửi cho người dùng cá nhân nếu có user_id
        if user_id:
            thread_id = user_id
            thread_type = ThreadType.USER 
        elif group_id:
            thread_id = group_id
            thread_type = ThreadType.GROUP
        else:
            print("❌ Error: Must provide either user_id or group_id.")
            raise ValueError("No recipient specified for Zalo message.")

        try:
            message_object = MessageObject(text=message)

            # Phương thức này của zlapi hoạt động cho cả hai
            self.client.sendMessage(message_object, thread_id, thread_type)

            print(f"✅ Sent message to Zalo {thread_type.name.lower()} {thread_id}")
        except Exception as e:
            print(f"❌ Failed to send Zalo message to {thread_id}: {e}")
            raise e

    def remove_user(self, group_id: str, user_id: str):
        if not self.client:
            print("❌ Zalo client not initialized. Cannot remove user.")
            return
        try:
            self.client.remove_members_from_group(group_id, [user_id])
            print(f"Removed user {user_id} from Zalo group {group_id}")
        except Exception as e:
            print(f"Failed to remove Zalo user: {e}")



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