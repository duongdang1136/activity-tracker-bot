import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from api.zalo_api import zalo_api_client
from services import ActivityService
import time

def run_zalo_listener():
    client = zalo_api_client.client
    if not client:
        print("❌ Zalo client not initialized. Listener will not start.")
        return

    activity_service = ActivityService()
    print("🤖 Zalo Listener is starting...")

    @client.onMessage
    def on_text_message(event):
        """Hàm này sẽ được tự động gọi khi có tin nhắn văn bản mới."""
        try:
            print(f"Received Zalo message from user: {event.author_id}")

            author_id = event.author_id
            thread_id = event.thread_id
            thread_type = event.thread_type

            # Chỉ xử lý các hoạt động trong nhóm
            if thread_type != 'GROUP':
                return

            # Lấy thông tin chi tiết để lưu vào DB 
            author_info = zalo_api_client.get_user_info(author_id)
            group_info = zalo_api_client.get_group_info(thread_id)

            author_name = author_info.name if author_info else "Unknown User"
            group_name = group_info.name if group_info else "Unknown Group"

            # Gọi service để ghi nhận hoạt động
            activity_service.track_message("Zalo", author_id, author_name, thread_id, group_name)
        except Exception as e:
            print(f"Error processing Zalo message event: {e}")

    #@client.onEvent
    #def on_reaction(event):
        # zlapi có thể không hỗ trợ trực tiếp event reaction, cần kiểm tra tài liệu
        # Giả lập ở đây
    #    print("Zalo reaction event received (simulation)")
        # activity_service.track_reaction(...)
        
    # Thêm các event khác như on_sticker, on_media nếu zlapi hỗ trợ

    # Vòng lặp lắng nghe
    while True:
        try:
            client.listen()
        except Exception as e:
            print(f"Error in Zalo listener loop: {e}. Reconnecting...")
            zalo_api_client._login() # Thử đăng nhập lại
            client = zalo_api_client.client
            time.sleep(10)