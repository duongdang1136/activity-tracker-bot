import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Thêm thư mục gốc vào path để có thể import các module khác
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from config import db_manager # Import db_manager từ package config

def fetch_and_print_ids():
    """
    Kết nối đến Supabase và in ra danh sách các nhóm cùng với ID cần thiết.
    """
    if not db_manager or not db_manager.client:
        print("❌ Không thể khởi tạo kết nối database.")
        return

    print("📡 Đang truy vấn dữ liệu từ Supabase...")
    
    try:
        # Sử dụng join để lấy thông tin từ cả hai bảng `platform_groups` và `platforms`
        # trong cùng một query.
        response = db_manager.client.from_('platform_groups').select('''
            id,
            group_name,
            group_platform_id,
            platforms (
                id,
                name
            )
        ''').execute()

        if response.data:
            print("\n" + "="*80)
            print("DANH SÁCH CÁC NHÓM ĐÃ GHI NHẬN TRONG DATABASE")
            print("="*80)
            print(f"{'Group Name':<30} | {'Platform':<10} | {'Group DB ID (UUID)':<38} | {'Platform DB ID'}")
            print("-"*80)
            
            for group in response.data:
                platform_info = group.get('platforms')
                if platform_info:
                    group_name = group.get('group_name', 'N/A')
                    platform_name = platform_info.get('name', 'N/A')
                    group_db_id = group.get('id', 'N/A')
                    platform_db_id = platform_info.get('id', 'N/A')
                    
                    print(f"{group_name[:28]:<30} | {platform_name:<10} | {group_db_id:<38} | {platform_db_id}")
            
            print("="*80)
            print("\n📋 Copy các giá trị 'Group DB ID' và 'Platform DB ID' vào biến `MANAGED_GROUPS` trong file `main.py`.")

        else:
            print("🤷 Không tìm thấy nhóm nào. Hãy chắc chắn rằng bot đã tương tác với ít nhất một nhóm.")

    except Exception as e:
        print(f"❌ Đã xảy ra lỗi khi truy vấn: {e}")


if __name__ == "__main__":
    fetch_and_print_ids()