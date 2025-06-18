# services/management_service.py (File mới)
from config.database import db_manager
from config.config import settings
from api.zalo_api import zalo_api_client
# from api.discord_api import discord_api_client # Sẽ tạo sau

class ManagementService:
    def __init__(self):
        # Mapping platform name to api client instance
        self.api_clients = {
            'zalo': zalo_api_client,
            # 'discord': discord_api_client 
        }

    def check_and_warn_inactive_users(self, group_internal_id: str, platform_internal_id: int, platform_name: str):
        """
        Kiểm tra một group cụ thể, tìm user inactive và gửi cảnh báo.
        Lưu ý: ID ở đây là UUID và ID số trong CSDL của bạn.
        """
        print(f"--- Running Inactive User Check for group {group_internal_id} on {platform_name} ---")
        inactive_users = db_manager.get_inactive_users_in_group(group_internal_id, platform_internal_id)

        if not inactive_users:
            print("No inactive users found.")
            return

        api_client = self.api_clients.get(platform_name.lower())
        if not api_client:
            print(f"No API client found for platform: {platform_name}")
            return

        for user in inactive_users:
            user_platform_id = user['user_platform_id']
            group_platform_id = user['group_platform_id']
            user_display_name = user['display_name']
            
            warn_message = (
                f"👋 Chào bạn {user_display_name},\n"
                f"Hệ thống ghi nhận bạn đã không hoạt động trong một thời gian dài. "
                f"Vui lòng tương tác để giữ vị trí trong nhóm nhé!"
            )
            
            print(f"⚠️ Sending warning to {user_display_name} ({user_platform_id})")
            # Với Zalo, không thể nhắn tin riêng, nên sẽ tag trong group
            api_client.send_message(group_platform_id, f"@{user_display_name} {warn_message}")
            # Ghi nhận lại thời điểm cảnh báo (cần thêm cột `last_warned_at` vào DB để tối ưu)