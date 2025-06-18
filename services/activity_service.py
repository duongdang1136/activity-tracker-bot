# services/activity_service.py
from config.database import db_manager

class ActivityService:
    def _track_activity(self, platform_name: str, user_id: str, user_name: str, group_id: str, group_name: str, activity_type: str):
        """Hàm private chung để tránh lặp code"""
        print(f"🔄 Tracking '{activity_type}' from '{user_name}' in '{group_name}' on {platform_name}")
        metadata = {'display_name': user_name, 'group_name': group_name}
        db_manager.record_activity(
            user_platform_id=user_id,
            platform_name=platform_name.lower(),
            group_platform_id=group_id,
            activity_type=activity_type,
            metadata=metadata
        )

    def track_message(self, platform_name: str, user_id: str, user_name: str, group_id: str, group_name: str):
        self._track_activity(platform_name, user_id, user_name, group_id, group_name, 'message')

    def track_reaction(self, platform_name: str, user_id: str, user_name: str, group_id: str, group_name: str):
        self._track_activity(platform_name, user_id, user_name, group_id, group_name, 'reaction')

    def track_sticker(self, platform_name: str, user_id: str, user_name: str, group_id: str, group_name: str):
        self._track_activity(platform_name, user_id, user_name, group_id, group_name, 'sticker')
        
    def track_media(self, platform_name: str, user_id: str, user_name: str, group_id: str, group_name: str):
        self._track_activity(platform_name, user_id, user_name, group_id, group_name, 'media') # Giả định 'media' là loại chung