import os
from dotenv import load_dotenv
from zlapi import ZaloAPI

# Nạp các biến môi trường từ file .env
# load_dotenv() sẽ tự động tìm file .env trong thư mục hiện tại
print("Loading .env file...")
load_dotenv()

# Lấy thông tin đăng nhập từ biến môi trường
ZALO_PHONE = os.getenv('ZALO_PHONE')
ZALO_PASSWORD = os.getenv('ZALO_PASSWORD')
ZALO_IMEI = os.getenv('ZALO_IMEI')
ZALO_COOKIES_STR = os.getenv('ZALO_COOKIES') # Cookies là chuỗi JSON

# Kiểm tra xem có lấy được thông tin không
if not all([ZALO_PHONE, ZALO_PASSWORD]):
    print("❌ Error: ZALO_PHONE and ZALO_PASSWORD must be set in .env file.")
else:
    print(f"Found credentials for phone: {ZALO_PHONE}")
    
    # Khối try...except để bắt mọi lỗi có thể xảy ra
    try:
        print("\nAttempting to initialize ZaloClient...")
        
        # Chuyển đổi chuỗi cookies thành dictionary nếu có
        import json
        cookies_dict = {}
        if ZALO_COOKIES_STR:
            try:
                cookies_dict = json.loads(ZALO_COOKIES_STR)
            except json.JSONDecodeError:
                print("⚠️ Warning: ZALO_COOKIES is not a valid JSON string. Using empty cookies.")

        # Khởi tạo client
        client = ZaloAPI(
            phone=ZALO_PHONE,
            password=ZALO_PASSWORD,
            imei=ZALO_IMEI,
            cookies=cookies_dict
        )
        
        print("✅ ZaloAPI initialized successfully!")
        print(f"   - Type of 'client' object is: {type(client)}")
        
        # ==========================================================
        # KHÁM NGHIỆM ĐỐI TƯỢNG 'client'
        # ==========================================================
        print("\n--- Inspecting the 'client' object ---")
        all_attributes = dir(client)
        
        public_methods = [attr for attr in all_attributes if not attr.startswith('_') and callable(getattr(client, attr))]
        
        print("Available public methods are:")
        for method_name in public_methods:
            print(f"  - {method_name}")
            
        print("\n--- Trying to call some methods ---")

        # Thử gọi một vài phương thức dựa trên kết quả khám nghiệm
        if 'get_my_profile' in public_methods:
            my_info = client.get_my_profile()
            print(f"  - get_my_profile() successful. Name: {my_info.name}")
        else:
            print("  - Method 'get_my_profile' does NOT exist.")

        if 'send_text_message' in public_methods:
            print("  - Method 'send_text_message' exists.")
        else:
            print("  - Method 'send_text_message' does NOT exist.")

    except Exception as e:
        print(f"\n❌ An error occurred during the process: {e}")