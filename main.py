import asyncio
import threading
import time
import schedule
import subprocess
import threading
import time
import sys
import os
from typing import List, Dict

# Import các hàm khởi động từ các module tương ứng
from bot.discord_bot import start_discord_bot
from bot.telegram_bot import start_telegram_bot
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
        'group_name': 'Đặng Gia (Zalo)', # Tên nhóm Zalo của bạn
        'group_db_id': '6799604717677589329', # <<--- THAY THẾ BẰNG groupid ZALO CỦA BẠN
        'platform_db_id': 1, # ID của platform 'Zalo' trong bảng platforms
        'platform_name': 'Zalo',
    },
    {
        'group_name': 'Trading Squad (Discord)', # Bạn có thể đặt tên bất kỳ để dễ nhận biết
        'group_db_id': '3a6c0697-041b-4212-9ce0-e95ec68f58b2', # groupid của Discord bạn cung cấp
        'platform_db_id': 2, # ID của platform 'Discord' trong bảng platforms
        'platform_name': 'Discord',
    },
    {
        'group_name': 'Đặng Gia (Zalo)', # Tên nhóm Zalo của bạn
        'group_db_id': '6799604717677589329', # <<--- THAY THẾ BẰNG groupid ZALO CỦA BẠN
        'platform_db_id': 3, # ID của platform 'Zalo' trong bảng platforms
        'platform_name': 'Telegram',
    },
    # Thêm các nhóm khác ở đây nếu có...
]

def run_zalo_bot_process():
    """
    Hàm này sẽ khởi chạy bot Zalo (Node.js) như một tiến trình con.
    """
    # Đường dẫn đến thư mục chứa script Node.js
    service_dir = os.path.join(os.path.dirname(__file__), 'bot', 'zalo_service')
    script_path = os.path.join(service_dir, 'index.js')

    # Lệnh để chạy Node.js
    # sys.executable là đường dẫn đến trình thông dịch Python hiện tại,
    # chúng ta sẽ tìm node.exe ở một vị trí tương đối hoặc trong PATH
    node_command = 'node' # Giả định 'node' có trong PATH của hệ thống

    print(f"🤖 Starting Zalo Bot Service process from: {service_dir}")

    # subprocess.Popen sẽ chạy lệnh trong một tiến trình mới và không block.
    # stdout=subprocess.PIPE và stderr=subprocess.PIPE để chúng ta có thể đọc log.
    process = subprocess.Popen(
        [node_command, script_path],
        stdout=sys.stdout, # Chuyển hướng log của Node.js ra terminal chính
        stderr=sys.stderr, # Chuyển hướng lỗi của Node.js ra terminal chính
        cwd=service_dir # Đặt thư mục làm việc cho tiến trình con
    )

    print(f"✅ Zalo Bot Service started with PID: {process.pid}")
    return process

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
    print("\n" + "*"*60)
    print("🚀 INITIALIZING ALL SERVICES (Python & Node.js) 🚀")
    print("*"*60)

    # --- 2. Khởi chạy các tiến trình/luồng đồng bộ ---

    # Chạy Zalo Bot (Node.js) trong một thread riêng để quản lý
    zalo_process = None
    def start_and_manage_zalo():
        nonlocal zalo_process
        zalo_process = run_zalo_bot_process()
        zalo_process.wait() # Chờ tiến trình kết thúc

    zalo_thread = threading.Thread(target=start_and_manage_zalo, name="ZaloProcessManager", daemon=True)

    web_thread = threading.Thread(target=run_web_app, name="WebApp", daemon=True)
    scheduler_thread = threading.Thread(target=run_scheduler, name="Scheduler", daemon=True)

    zalo_thread.start()
    web_thread.start()
    scheduler_thread.start()

    # --- 3. Khởi chạy các bot bất đồng bộ của Python ---
    discord_task = asyncio.create_task(start_discord_bot(), name="DiscordBotTask")
    telegram_task = asyncio.create_task(start_telegram_bot(), name="TelegramBotTask")

    print("✅ All components are starting...")
    try:
        await asyncio.gather(discord_task, telegram_task)
    finally:
        # --- 4. Dọn dẹp khi chương trình chính kết thúc ---
        print("\n🛑 Shutting down... Terminating Zalo Bot process.")
        if zalo_process:
            zalo_process.terminate() # Gửi tín hiệu để tắt tiến trình Node.js


if __name__ == "__main__":
    try:

        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 System shutdown requested by user. Goodbye!")


