# bot/zalo_listener.py (File mới)
from api.zalo_api import zalo_api_client
from services.activity_service import ActivityService
import time

def run_zalo_listener():
    client = zalo_api_client.client
    if not client:
        print("❌ Zalo client not initialized. Listener will not start.")
        return

    activity_service = ActivityService()
    print("🤖 Zalo Listener is starting...")

    @client.event
    def on_text_message(event):
        author_id = event.author_id
        author_name = client.get_user_info(author_id).name # Lấy tên user
        group_id = event.thread_id
        group_name = client.get_thread_info(group_id).name # Lấy tên group
        
        activity_service.track_message("Zalo", author_id, author_name, group_id, group_name)

    @client.event
    def on_reaction(event):
        # zlapi có thể không hỗ trợ trực tiếp event reaction, cần kiểm tra tài liệu
        # Giả lập ở đây
        print("Zalo reaction event received (simulation)")
        # activity_service.track_reaction(...)
        
    # Thêm các event khác như on_sticker, on_media nếu zlapi hỗ trợ

    # Vòng lặp lắng nghe
    while True:
        try:
            client.listen()
        except Exception as e:
            print(f"Error in Zalo listener loop: {e}. Reconnecting...")
            zalo_api_client._login() # Thử đăng nhập lại
            time.sleep(10)