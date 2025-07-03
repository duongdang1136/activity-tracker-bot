import sys
import os
import time
from datetime import datetime, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api import zalo_api_client
from services import activity_service
from config import db_manager


PLATFORM_ID_ZALO = 1 

def _handle_linking_token(event) -> bool:
    """
    Hàm xử lý mã liên kết với các bước debug chi tiết.
    """
    message_text = event.message.text.strip().upper()
    
    if ' ' in message_text or len(message_text) > 10:
        return False

    print(f"\n--- DEBUG: Bắt đầu xử lý token '{message_text}' ---")
    
    try:
        platform_id_zalo = 1
        
        # BƯỚC 1: Tìm token
        print(f"[1] Đang tìm token '{message_text}' cho platform_id={platform_id_zalo}...")
        response = db_manager.client.from_('platform_linking_tokens').select('*')\
            .eq('token', message_text)\
            .eq('platform_id', platform_id_zalo)\
            .eq('is_used', False)\
            .limit(1).execute()

        if not response.data:
            print("[1.1] Không tìm thấy token hợp lệ. Bỏ qua.")
            return False
        
        token_data = response.data[0]
        print(f"[1.2] ✅ Tìm thấy token! Dữ liệu: {token_data}")

        # BƯỚC 2: Kiểm tra hết hạn
        print("[2] Đang kiểm tra thời gian hết hạn...")
        from datetime import datetime, timezone
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            print("[2.1] ❌ Token đã hết hạn.")
            zalo_api_client.send_message(message="Mã liên kết của bạn đã hết hạn. Vui lòng vào website để tạo một mã mới.", user_id=event.author_id)
            db_manager.client.from_('platform_linking_tokens').update({'is_used': True}).eq('id', token_data['id']).execute()
            return True

        print("[2.2] ✅ Token còn hạn.")
        
        # BƯỚC 3: Chuẩn bị dữ liệu để liên kết
        super_user_id = token_data['user_id']
        zalo_platform_user_id = event.author_id
        
        print(f"[3] Chuẩn bị liên kết: super_user_id='{super_user_id}', zalo_id='{zalo_platform_user_id}'")
        
        author_info = zalo_api_client.get_user_info(zalo_platform_user_id)
        zalo_username = author_info.name if author_info else "Zalo User"
        print(f"[3.1] Lấy được tên Zalo: '{zalo_username}'")

        # BƯỚC 4: Thực hiện INSERT vào user_platform_profiles
        print("[4] Đang thực hiện INSERT vào user_platform_profiles...")
        insert_response = db_manager.client.from_('user_platform_profiles').insert({
            'user_id': super_user_id,
            'platform_id': platform_id_zalo,
            'platform_user_id': zalo_platform_user_id,
            'platform_username': zalo_username
        }).execute()

        # Kiểm tra kết quả của lệnh INSERT
        if not insert_response.data:
             print(f"[4.1] ❌ Lệnh INSERT thất bại! Lỗi từ Supabase: {insert_response.error}")
             raise Exception(f"Failed to insert into user_platform_profiles: {insert_response.error.message if insert_response.error else 'Unknown error'}")

        print("[4.2] ✅ INSERT vào user_platform_profiles thành công.")

        # BƯỚC 5: Đánh dấu token đã sử dụng
        print("[5] Đang cập nhật token thành is_used = true...")
        update_response = db_manager.client.from_('platform_linking_tokens').update({'is_used': True}).eq('id', token_data['id']).execute()
        
        if not update_response.data:
            print(f"[5.1] ❌ Lệnh UPDATE token thất bại! Lỗi từ Supabase: {update_response.error}")
            # Dù bước này lỗi, ta vẫn nên coi như đã thành công để báo cho user
        else:
            print("[5.2] ✅ UPDATE token thành công.")

        # BƯỚC 6: Gửi tin nhắn xác nhận
        print("[6] Đang gửi tin nhắn xác nhận thành công...")
        zalo_api_client.send_message(message="Chúc mừng! Tài khoản Zalo của bạn đã được liên kết thành công với hệ thống của chúng tôi.", user_id=event.author_id)
        
        print(f"--- DEBUG: Hoàn tất xử lý token '{message_text}' thành công. ---")
        return True

    except Exception as e:
        # Nếu có bất kỳ lỗi nào xảy ra trong chuỗi xử lý trên, nó sẽ được bắt ở đây
        print(f"--- DEBUG: GẶP LỖI TRONG KHỐI TRY ---")
        print(f"❌ Error during Zalo account linking process: {e}")
        try:
            zalo_api_client.send_message(message="Đã có lỗi xảy ra trong quá trình xử lý mã liên kết của bạn. Vui lòng thử lại sau.", user_id=event.author_id)
        except:
            pass
        return True

def _handle_activity_message(event):
    """
    Xử lý tin nhắn hoạt động thông thường để ghi điểm.
    """
    try:
        author_id = event.author_id
        thread_id = event.thread_id
        thread_type = event.thread_type

        # Chỉ tính điểm cho hoạt động trong nhóm
        if thread_type != 'GROUP':
            return

        author_info = zalo_api_client.get_user_info(author_id)
        group_info = zalo_api_client.get_group_info(thread_id)
        
        author_name = author_info.name if author_info else author_id
        group_name = group_info.name if group_info else thread_id
        
        activity_service.track_message("Zalo", author_id, author_name, thread_id, group_name)
    except Exception as e:
        print(f"Error processing Zalo activity message: {e}")


def run_zalo_listener():
    """
    Hàm chính để khởi chạy Zalo listener.
    """
    client = zalo_api_client.client
    if not client:
        print("❌ Zalo client not initialized. Zalo listener will not start.")
        return

    print("🤖 Zalo Listener is starting...")

    def on_zalo_text_message(event):
        """
        Hàm điều phối: Được gọi mỗi khi có tin nhắn văn bản mới.
        """
        # Ưu tiên kiểm tra xem có phải là mã liên kết không
        is_token_handled = _handle_linking_token(event)
        
        # Nếu không phải là tin nhắn chứa mã liên kết, thì xử lý nó như một hoạt động bình thường
        if not is_token_handled:
            _handle_activity_message(event)

    # Đăng ký hàm điều phối với sự kiện "onTextMessage"
    client.onEvent("onTextMessage", on_zalo_text_message)
    print("✅ Zalo 'onTextMessage' event handler (with linking logic) registered.")

    # Vòng lặp chính để lắng nghe sự kiện từ Zalo
    while True:
        try:
            print("Zalo listener is waiting for events...")
            client.listen()
        except KeyboardInterrupt:
            print("\nZalo listener stopped by user.")
            break
        except Exception as e:
            print(f"An error occurred in Zalo listener loop: {e}. Attempting to reconnect...")
            zalo_api_client._login()
            client = zalo_api_client.client # Cập nhật lại đối tượng client
            if not client:
                print("Failed to reconnect Zalo client. Stopping Zalo listener thread.")
                break
            time.sleep(15) # Đợi một chút trước khi thử lắng nghe lại