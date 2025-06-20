import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import supabase
from config import settings

class DatabaseManager:
    def __init__(self):
        try:
            self.client = supabase.create_client(settings.supabase.url, settings.supabase.key)
            print("✅ Database connection initialized.")
        except Exception as e:
            print(f"❌ Failed to initialize database connection: {e}")
            self.client = None

    def record_activity(self, user_platform_id: str, platform_name: str, group_platform_id: str, activity_type: str, metadata: dict = None):
        if not self.client:
            print("❌ Database client not available. Cannot record activity.")
            return

        print(f"📡 Calling RPC 'update_activity_with_group' for user {user_platform_id} on {platform_name}")
        try:
            rpc_params = {
                'p_user_platform_id': user_platform_id,
                'p_platform_name': platform_name,
                'p_group_platform_id': group_platform_id,
                'p_activity_type': activity_type,
                'p_metadata': metadata or {}
            }
            response = self.client.rpc('update_activity_with_group', rpc_params).execute()

            if hasattr(response, 'error') and response.error:
                 print(f"❌ RPC Error: {response.error.message}")
            else:
                 print("✅ Activity recorded successfully via RPC.")

        except Exception as e:
            print(f"❌ An error occurred while calling RPC: {e}")

    def get_group_leaderboard(self, group_name: str, platform_name: str):
        if not self.client:
            print("❌ Database client not available.")
            return None
        try:
            response = self.client.from_('group_leaderboard_with_roles').select('*').eq('group_name', group_name).eq('platform_name', platform_name).order('rank_in_group', desc=False).execute()
            return response.data
        except Exception as e:
            print(f"❌ Error fetching leaderboard: {e}")
            return None
# config/database.py

# ... trong class DatabaseManager ...
    def get_inactive_users_in_group(self, group_id: str, platform_id: int):
        """Lấy danh sách user có status 'inactive' trong một group cụ thể."""
        if not self.client: return []
        try:
            # Chúng ta cần join nhiều bảng để lấy thông tin cần thiết
            # user_platform_id, display_name, v.v.
            response = self.client.rpc('get_inactive_members', {
                'p_group_id': group_id,
                'p_platform_id': platform_id
            }).execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"Error calling get_inactive_members RPC: {response.error.message}")
                return []
            return response.data
        except Exception as e:
            print(f"Error fetching inactive users: {e}")
            return []



db_manager = DatabaseManager()
