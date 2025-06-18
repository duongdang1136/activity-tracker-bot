from config.database import db_manager

class WebService:
    def get_leaderboard_for_group(self, group_name: str, platform_name: str):
        print(f"📈 Fetching leaderboard for {group_name} on {platform_name}")
        return db_manager.get_group_leaderboard(group_name, platform_name.capitalize())
