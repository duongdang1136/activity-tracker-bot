import asyncio
from config import db_manager, settings
from api import telegram_api_client, zalo_api_client
try:
    from bot.discord_bot import DiscordApiClient
except ImportError:
    print("Warning: Discord API client not available. Management for Discord will be skipped.")
    discord_api_client = None

class ManagementService:
    """
    Dịch vụ quản lý thành viên tự động.
    - Cảnh báo người dùng không hoạt động.
    - Xóa người dùng không hoạt động sau cảnh báo.
    """
    def __init__(self):
        # Mapping platform name to the corresponding async API client
        # Điều này cho phép chúng ta gọi client một cách linh hoạt dựa trên tên platform
        self.api_clients = {
            'discord': discord_api_client,
            'telegram': telegram_api_client,
            'zalo': zalo_api_client
        }
        print("✅ ManagementService initialized with available API clients.")

    async def _process_group(self, group_config: dict, action: str):
        """
        Hàm xử lý chung cho một nhóm, thực hiện một hành động cụ thể ('warn' hoặc 'kick').
        """
        group_db_id = group_config.get('group_db_id')
        platform_db_id = group_config.get('platform_db_id')
        platform_name = group_config.get('platform_name', '').lower()

        if not all([group_db_id, platform_db_id, platform_name]):
            print(f"❌ Invalid group configuration: {group_config}")
            return

        api_client = self.api_clients.get(platform_name)
        if not api_client:
            print(f"⚠️ No API client configured for platform '{platform_name}'. Skipping.")
            return

        print(f"--- Processing group '{group_config.get('group_name', 'N/A')}' on {platform_name.upper()} for action: {action.upper()} ---")

        # Lấy danh sách user không hoạt động từ database
        # (Giả sử hàm RPC `get_inactive_members` đã tồn tại trong DB)
        inactive_users = db_manager.get_inactive_users_in_group(group_db_id, platform_db_id)

        if not inactive_users:
            print("✅ No inactive users found. Nothing to do.")
            return

        tasks = []
        for user in inactive_users:
            user_platform_id = user.get('user_platform_id')
            group_platform_id = user.get('group_platform_id')
            user_display_name = user.get('display_name', 'member')

            if action == 'warn':
                warn_message = (
                    f"👋 Chào bạn {user_display_name},\n"
                    f"Hệ thống ghi nhận bạn đã không hoạt động trong một thời gian dài. "
                    f"Vui lòng tương tác trong vòng {settings.bot.inactive_warn_days} ngày tới để giữ vị trí trong nhóm nhé!"
                )
                print(f" vysok Preparing to WARN user '{user_display_name}' ({user_platform_id}).")
                # Tạo một coroutine để gửi tin nhắn
                task = api_client.send_message(group_platform_id, warn_message)
                tasks.append(task)
                # TODO: Cập nhật CSDL rằng người dùng này đã được cảnh báo (ví dụ: cột last_warned_at)

            elif action == 'kick':
                print(f"🚨 Preparing to KICK user '{user_display_name}' ({user_platform_id}).")
                # Tạo một coroutine để kick người dùng
                task = api_client.remove_user(group_platform_id, user_platform_id)
                tasks.append(task)
                # TODO: Cập nhật CSDL rằng người dùng này đã bị xóa (ví dụ: `is_active=false` trong group_memberships)

        # Chạy tất cả các tác vụ (gửi tin, kick) một cách đồng thời để tăng hiệu suất
        if tasks:
            print(f"🚀 Executing {len(tasks)} tasks concurrently...")
            await asyncio.gather(*tasks, return_exceptions=True)
            print("✅ All tasks executed.")

    async def run_warning_cycle(self, managed_groups: list):
        """
        Chạy chu trình cảnh báo cho tất cả các nhóm được quản lý.
        """
        print("\n" + "="*50)
        print("🔄 STARTING INACTIVE USER WARNING CYCLE 🔄")
        print("="*50)
        for group_config in managed_groups:
            await self._process_group(group_config, action='warn')
        print("="*50)
        print("✅ FINISHED INACTIVE USER WARNING CYCLE ✅")
        print("="*50 + "\n")

    async def run_kick_cycle(self, managed_groups: list):
        """
        Chạy chu trình xóa thành viên cho tất cả các nhóm được quản lý.
        (Nên chạy sau chu trình cảnh báo một khoảng thời gian)
        """
        print("\n" + "="*50)
        print("🚨 STARTING INACTIVE USER KICK CYCLE 🚨")
        print("="*50)
        for group_config in managed_groups:
            await self._process_group(group_config, action='kick')
        print("="*50)
        print("✅ FINISHED INACTIVE USER KICK CYCLE ✅")
        print("="*50 + "\n")