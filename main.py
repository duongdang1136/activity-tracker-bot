# main.py (File mới ở thư mục gốc)
import threading
import time
import schedule
from bot.main import run_bot as run_discord_bot
from bot.zalo_listener import run_zalo_listener
from web.app import run_web_app
from services.management_service import ManagementService
from config.config import settings

def run_management_tasks():
    """Hàm chạy các tác vụ quản lý định kỳ."""
    management_service = ManagementService()
    
    # --- CẤU HÌNH NHÓM CẦN QUẢN LÝ ---
    # Thay bằng ID thực tế từ database của bạn
    # Ví dụ: group UUID '...' và platform ID 1 (giả sử 1 là Zalo)
    managed_groups = [
        {'group_db_id': 'uuid-cua-nhom-zalo-1', 'platform_db_id': 1, 'platform_name': 'Zalo'},
        # {'group_db_id': 'uuid-cua-nhom-zalo-2', 'platform_db_id': 1, 'platform_name': 'Zalo'},
    ]
    
    for group in managed_groups:
        management_service.check_and_warn_inactive_users(
            group['group_db_id'], 
            group['platform_db_id'], 
            group['platform_name']
        )

def schedule_management_jobs():
    """Lên lịch cho các tác vụ."""
    print(f"🕒 Scheduling management job to run every {settings.bot.management_check_interval_hours} hours.")
    
    schedule.every(settings.bot.management_check_interval_hours).hours.do(run_management_tasks)
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Kiểm tra mỗi phút

if __name__ == "__main__":
    # Mỗi thành phần sẽ chạy trên một luồng (thread) riêng
    discord_thread = threading.Thread(target=run_discord_bot, name="DiscordBot")
    zalo_thread = threading.Thread(target=run_zalo_listener, name="ZaloListener")
    web_thread = threading.Thread(target=run_web_app, name="WebApp")
    scheduler_thread = threading.Thread(target=schedule_management_jobs, name="Scheduler")

    print("--- Starting All System Components ---")
    
    # Bắt đầu các luồng
    discord_thread.start()
    zalo_thread.start()
    web_thread.start()
    scheduler_thread.start()

    # Giữ luồng chính chạy
    discord_thread.join()
    zalo_thread.join()
    web_thread.join()
    scheduler_thread.join()

    print("--- System Shutdown ---")