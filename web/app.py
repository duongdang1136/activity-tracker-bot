import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from config import db_manager
from services import WebService
from api import zalo_api_client
import random
import time
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
CORS(app) # Cho phép cross-origin requests
bcrypt = Bcrypt(app) # Khởi tạo bcrypt

web_service = WebService()
# ==============================================================================
# API LEADERBOARD (Đã có)
# ==============================================================================
@app.route('/api/leaderboard/<platform_name>/<group_name>', methods=['GET'])
def get_leaderboard(platform_name, group_name):
    data = web_service.get_leaderboard_for_group(group_name, platform_name)
    if data is None:
        return jsonify({"error": "Could not fetch leaderboard data."}), 500
    return jsonify(data)

# ==============================================================================
# API MỚI: ĐĂNG KÝ, ĐĂNG NHẬP, LIÊN KẾT
# ==============================================================================

# --- API Đăng ký ---
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('display_name'):
        return jsonify({"error": "Missing email, password, or display_name"}), 400

    email = data['email']
    display_name = data['display_name']
    # Hash mật khẩu trước khi lưu vào DB
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    try:
        # Thực hiện INSERT vào bảng users
        response = db_manager.client.from_('users').insert({
            'email': email,
            'hashed_password': hashed_password,
            'display_name': display_name
        }).execute()

        # Kiểm tra xem có lỗi từ Supabase không (ví dụ: email đã tồn tại)
        if response.data:
            # Không trả về mật khẩu
            new_user = response.data[0]
            del new_user['hashed_password']
            return jsonify({"message": "User registered successfully", "user": new_user}), 201
        else:
            # Lỗi này có thể cần được phân tích kỹ hơn từ `response.error`
            return jsonify({"error": "Failed to register user. Email might already exist."}), 409

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- API Đăng nhập (sẽ cần JWT sau này, giờ làm đơn giản) ---
@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400

    email = data['email']
    password = data['password']

    try:
        # Tìm user bằng email
        response = db_manager.client.from_('users').select('*').eq('email', email).limit(1).execute()
        
        if not response.data:
            return jsonify({"error": "Invalid credentials"}), 401
            
        user = response.data[0]
        # So sánh mật khẩu đã hash
        if bcrypt.check_password_hash(user['hashed_password'], password):
            # Đăng nhập thành công
            # (Trong thực tế, đây là lúc bạn sẽ tạo và trả về một JWT token)
            del user['hashed_password']
            return jsonify({"message": "Login successful", "user": user}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# API LIÊN KẾT TÀI KHOẢN (MỞ RỘNG)
# ==============================================================================
def _link_platform_account(user_id: str, platform_id: int, platform_name: str, platform_user_id: str, platform_username: str): 
    #"""Hàm private chung để xử lý logic liên kết, tránh lặp code."""
    try:
        response = db_manager.client.from_('user_platform_profiles').insert({
            'user_id': user_id,
            'platform_id': platform_id,
            'platform_user_id': platform_user_id,
            'platform_username': platform_username
        }).execute()
        
        if response.data:
            return jsonify({"message": f"{platform_name.capitalize()} account linked successfully"}), 200
        else:
            error_message = response.error.message if response.error else "Unknown error." # Phân tích lỗi cụ thể hơn từ Supabase nếu có
            if 'duplicate key value violates unique constraint' in error_message:
                return jsonify({"error": f"Failed to link account. This {platform_name} account might be already linked."}), 409
            return jsonify({"error": f"Failed to link account: {error_message}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/<user_id>/link-discord', methods=['POST']) # API Liên kết Discord
def link_discord_account(user_id):
    """
    MOCK API: Liên kết tài khoản Discord.
    Frontend gửi lên discord_id và discord_username.
    """
    data = request.get_json()
    if not data or not data.get('discord_id') or not data.get('discord_username'):
        return jsonify({"error": "Missing discord_id or discord_username"}), 400
        
    platform_id_discord = 2 # Giả sử ID của Discord trong bảng `platforms` là 2
    return _link_platform_account(
        user_id,
        platform_id_discord,
        "discord",
        data['discord_id'],
        data['discord_username']
    )

# --- API: Liên kết Telegram ---
@app.route('/api/users/<user_id>/link-telegram', methods=['POST'])
def link_telegram_account(user_id):
    """
    MOCK API: Liên kết tài khoản Telegram.
    Frontend gửi lên telegram_id và telegram_username.
    """
    data = request.get_json()
    if not data or not data.get('telegram_id') or not data.get('telegram_username'):
        return jsonify({"error": "Missing telegram_id or telegram_username"}), 400
        
    platform_id_telegram = 3 # Giả sử ID của Telegram trong bảng `platforms` là 3
    return _link_platform_account(
        user_id,
        platform_id_telegram,
        "telegram",
        data['telegram_id'],
        data['telegram_username']
    )

# ==============================================================================
# TẢI VÀ CACHE PLATFORM IDS KHI ỨNG DỤNG KHỞI ĐỘNG
# ==============================================================================
PLATFORM_IDS = {}
try:
    print("Loading platform IDs from database...")
    # Truy vấn bảng 'platforms' để lấy id và name
    response = db_manager.client.from_('platforms').select('id, name').execute()
    if response.data:
        # Lưu kết quả vào dictionary PLATFORM_IDS
        # Ví dụ: {'zalo': 1, 'discord': 2, 'telegram': 3}
        for p in response.data:
            PLATFORM_IDS[p['name']] = p['id']
        print(f"✅ Platform IDs loaded successfully: {PLATFORM_IDS}")
    else:
        print("⚠️ No platforms found in the database.")
except Exception as e:
    print(f"❌ Critical error: Could not load platform IDs. Management features may fail. Error: {e}")


#TEST_ZALO_PHONE = "0911002100"
#TEST_ZALO_OTP = "999999"


# ==============================================================================
# API LIÊN KẾT ZALO (SỬ DỤNG DATABASE)
# ==============================================================================

# --- API Yêu cầu mã xác thực Zalo ---
@app.route('/api/users/<user_id>/link-zalo/request-code', methods=['POST'])
def request_zalo_link_code(user_id):
    data = request.get_json()
    phone_number = data.get('phone_number')
    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400
    """
    # LOGIC MỚI: KIỂM TRA SỐ ĐIỆN THOẠI TEST
    # ==========================================================
    if phone_number == TEST_ZALO_PHONE:
        # Nếu là số điện thoại test, chỉ cần lưu OTP test và trả về thành công
        # Không cần gửi tin nhắn Zalo thật
        PLATFORM_IDS.get('zalo', 1) == {
            "code": TEST_ZALO_OTP,
            "phone": phone_number,
            "expires_at": time.time() + 300 # Vẫn có thời gian hết hạn
        }
        print(f"✅ Test mode: Bypassed Zalo message for test phone number {phone_number}.")
        return jsonify({"message": "Test verification code generated."}), 200
        """
    
    otp_code = str(random.randint(100000, 999999))
    hashed_otp = bcrypt.generate_password_hash(otp_code).decode('utf-8')     # Hash mã OTP trước khi lưu vào DB để tăng bảo mật
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)    # Đặt thời gian hết hạn là 5 phút kể từ bây giờ

    try:
        data_to_upsert = {
            'user_id': user_id,
            'phone_number': phone_number,
            'otp_code': hashed_otp,
            'expires_at': expires_at.isoformat()
        }
        
        response = db_manager.client.from_('otp_codes').upsert(
            data_to_upsert,
            on_conflict='user_id,phone_number' 
        ).execute()
        
        
        # Gửi mã OTP chưa hash đến người dùng
        message = f"Mã xác thực liên kết tài khoản Zalo của bạn là: {otp_code}. Mã có hiệu lực trong 5 phút."
        zalo_api_client.send_message(user_id=phone_number, message=message)
        
        print(f"Sent Zalo OTP to {phone_number} for user {user_id}")
        return jsonify({"message": "Verification code sent to your Zalo."}), 200

    except Exception as e:
        print(f"Error handling Zalo OTP request: {e}")
        return jsonify({"error": "Failed to process verification code request."}), 500


# --- API Xác thực mã và hoàn tất liên kết Zalo ---
@app.route('/api/users/<user_id>/link-zalo/verify-code', methods=['POST'])
def verify_zalo_link_code(user_id):
    data = request.get_json()
    phone_number = data.get('phone_number')
    code_from_user = data.get('code')
    if not phone_number or not code_from_user:
        return jsonify({"error": "Phone number and code are required"}), 400

    try:
        # Tìm bản ghi OTP trong DB
        response = db_manager.client.from_('otp_codes').select('*').eq('user_id', user_id).eq('phone_number', phone_number).limit(1).execute()

        if not response.data:
            return jsonify({"error": "No verification process started for this user/phone number."}), 404
        
        otp_record = response.data[0]
        
        # Chuyển đổi thời gian hết hạn từ chuỗi về đối tượng datetime
        expires_at = datetime.fromisoformat(otp_record['expires_at'])

        # Kiểm tra: mã có khớp không VÀ chưa hết hạn
        if bcrypt.check_password_hash(otp_record['otp_code'], code_from_user) and datetime.now(timezone.utc) < expires_at:
            
            # Xóa mã OTP đã dùng khỏi DB để tránh dùng lại
            db_manager.client.from_('otp_codes').delete().eq('id', otp_record['id']).execute()
            
            # --- Logic liên kết tài khoản (không đổi) ---
            platform_id_zalo = PLATFORM_IDS.get('zalo', 1)
            zalo_user_info = zalo_api_client.get_user_info(phone_number)
            zalo_username = zalo_user_info.name if zalo_user_info else "Zalo User"

            response, status_code = _link_platform_account(
                user_id, platform_id_zalo, "zalo", phone_number, zalo_username
            )
            return response, status_code
        else:
            return jsonify({"error": "Invalid or expired verification code."}), 400

    except Exception as e:
        print(f"Error verifying Zalo OTP: {e}")
        return jsonify({"error": "Failed to verify code."}), 500

def run_web_app():
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_web_app()
