import asyncio
import threading
import time
import schedule
from typing import List, Dict

# Import các hàm khởi động từ các module tương ứng
from bot.discord_bot import start_discord_bot
from bot.telegram_bot import start_telegram_bot
from bot.zalo_listener import run_zalo_listener
from web.app import run_web_app
from services import management_service
from config import settings

# ==============================================================================
# CẤU HÌNH TRUNG TÂM CHO CÁC NHÓM CẦN QUẢN LÝ
# ==============================================================================
# Thay thế các giá trị UUID và ID này bằng dữ liệu thực tế từ database của bạn.
# Bạn có thể lấy các ID này từ bảng `platform_groups` và `platforms` trong Supabase.
MANAGED_GROUPS: List[Dict] = [
    {
        'group_name': 'Trading Squad (Discord)', # Bạn có thể đặt tên bất kỳ để dễ nhận biết
        'group_db_id': '3a6c0697-041b-4212-9ce0-e95ec68f58b2', # groupid của Discord bạn cung cấp
        'platform_db_id': 2, # ID của platform 'Discord' trong bảng platforms
        'platform_name': 'Discord',
    },
    {
        'group_name': 'Đặng Gia (Zalo)', # Tên nhóm Zalo của bạn
        'group_db_id': '6799604717677589329', # <<--- THAY THẾ BẰNG groupid ZALO CỦA BẠN
        'platform_db_id': 1, # ID của platform 'Zalo' trong bảng platforms
        'platform_name': 'Zalo',
    },
    # Thêm các nhóm khác ở đây nếu có...
]

# ==============================================================================
# CÁC HÀM TÁC VỤ ĐỊNH KỲ (SCHEDULED TASKS)
# ==============================================================================

def scheduled_warning_job():
    """Hàm wrapper đồng bộ để chạy tác vụ cảnh báo bất đồng bộ."""
    print(f"⏰ Kicking off scheduled job: [Warning Cycle]")
    try:
        # Chạy coroutine từ một ngữ cảnh đồng bộ
        asyncio.run(management_service.run_warning_cycle(MANAGED_GROUPS))
    except Exception as e:
        print(f"❌ Error during scheduled warning job: {e}")

def scheduled_kick_job():
    """Hàm wrapper đồng bộ để chạy tác vụ kick bất đồng bộ."""
    print(f"⏰ Kicking off scheduled job: [Kick Cycle]")
    try:
        asyncio.run(management_service.run_kick_cycle(MANAGED_GROUPS))
    except Exception as e:
        print(f"❌ Error during scheduled kick job: {e}")

def run_scheduler():
    "Thiết lập và chạy vòng lặp cho các tác vụ định kỳ.Hàm này sẽ chạy trong một thread riêng."
    print("🕒 Scheduler is running in standby mode (Discovery Mode).")
    #print("🕒 Scheduler starting...")
    #schedule.every().day.at("08:00").do(scheduled_warning_job) # Lên lịch cảnh báo: Chạy mỗi ngày vào lúc 08:00       
    #schedule.every().monday.at("10:00").do(scheduled_kick_job) # Lên lịch kick: Chạy mỗi thứ Hai đầu tuần vào lúc 10:00  
    #print("🚀 Running initial warning cycle for testing...") # Chạy lần đầu ngay khi khởi động để test
    #scheduled_warning_job()

    while True:
        schedule.run_pending()
        time.sleep(60) # Kiểm tra lịch mỗi 60 giây

# ==============================================================================
# HÀM CHÍNH ĐỂ KHỞI ĐỘNG HỆ THỐNG
# ==============================================================================

async def main():
    """
    Hàm chính bất đồng bộ, điều phối khởi động tất cả các thành phần.
    """
    print("\n" + "*"*60)
    print("🚀 INITIALIZING MULTI-PLATFORM BOT SYSTEM 🚀")
    print("*"*60)

    # Các tác vụ đồng bộ (sync) cần chạy trong thread riêng để không block vòng lặp async
    # `daemon=True` đảm bảo các thread này sẽ tự động tắt khi chương trình chính kết thúc
    
    
    zalo_thread = threading.Thread(target=run_zalo_listener, name="ZaloListener", daemon=True) # 1. Chạy Zalo Listener (thư viện zlapi là sync)
    web_thread = threading.Thread(target=run_web_app, name="WebApp", daemon=True) # 2. Chạy Web App (Flask là sync)
    scheduler_thread = threading.Thread(target=run_scheduler, name="Scheduler", daemon=True) # 3. Chạy Scheduler (thư viện schedule là sync)
    # Bắt đầu các thread đồng bộ
    zalo_thread.start()
    web_thread.start()
    scheduler_thread.start()
    
    # Các tác vụ bất đồng bộ (async) có thể chạy cùng nhau trong vòng lặp sự kiện chính    
    # 1. Chạy Discord Bot (discord.py là async)
    discord_task = asyncio.create_task(start_discord_bot(), name="DiscordBotTask")    
    # 2. Chạy Telegram Bot (python-telegram-bot là async)
    telegram_task = asyncio.create_task(start_telegram_bot(), name="TelegramBotTask")
    # Chờ tất cả các tác vụ async hoàn thành (trong trường hợp này là mãi mãi, cho đến khi có lỗi)
    await asyncio.gather(discord_task, telegram_task)

if __name__ == "__main__":
    try:
        # Bắt đầu vòng lặp sự kiện bất đồng bộ
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 System shutdown requested by user. Goodbye!")
    except Exception as e:
        print(f"\n💥 A critical error occurred in the main event loop: {e}")