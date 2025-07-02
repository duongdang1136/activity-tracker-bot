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



def _link_platform_account(user_id: str, platform_id: int, platform_name: str, platform_user_id: str, platform_username: str): # API LIÊN KẾT TÀI KHOẢN (MỞ RỘNG)
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

# --- API: Liên kết Zalo ---
@app.route('/api/users/<user_id>/link-zalo', methods=['POST'])
def link_zalo_account(user_id):
    """
    MOCK API: Liên kết tài khoản Zalo.
    Frontend gửi lên zalo_id (chính là số điện thoại).
    """
    data = request.get_json()
    if not data or not data.get('zalo_id') or not data.get('zalo_username'):
        return jsonify({"error": "Missing zalo_id or zalo_username"}), 400
        
    platform_id_zalo = 1 # Giả sử ID của Zalo trong bảng `platforms` là 1
    return _link_platform_account(
        user_id,
        platform_id_zalo,
        "zalo",
        data['zalo_id'],
        data['zalo_username']
    )

@app.route('/api/users/<user_id>/link-zalo/request-code', methods=['POST'])
def request_zalo_link_code(user_id):
    data = request.get_json()
    phone_number = data.get('phone_number')
    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    # Tạo mã OTP 6 chữ số
    otp_code = str(random.randint(100000, 999999))
    
    # Lưu OTP tạm thời (hết hạn sau 300 giây = 5 phút)
    OTP_STORE[user_id] = {
        "code": otp_code,
        "phone": phone_number,
        "expires_at": time.time() + 300
    }
    
    try:
        # Gửi tin nhắn chứa mã OTP đến người dùng
        message = f"Mã xác thực liên kết tài khoản của bạn là: {otp_code}. Mã có hiệu lực trong 5 phút."
        # Lưu ý: user_id cho Zalo chính là số điện thoại
        zalo_api_client.send_message(user_id=phone_number, message=message)
        
        print(f"Sent Zalo OTP {otp_code} to {phone_number} for user {user_id}")
        return jsonify({"message": "Verification code sent to your Zalo."}), 200

    except Exception as e:
        print(f"Error sending Zalo OTP: {e}")
        return jsonify({"error": "Failed to send verification code. Please check the phone number."}), 500


# --- API MỚI: Xác thực mã và hoàn tất liên kết Zalo ---
@app.route('/api/users/<user_id>/link-zalo/verify-code', methods=['POST'])
def verify_zalo_link_code(user_id):
    data = request.get_json()
    phone_number = data.get('phone_number')
    code = data.get('code')
    if not phone_number or not code:
        return jsonify({"error": "Phone number and code are required"}), 400

    # Lấy thông tin OTP đã lưu
    stored_otp_info = OTP_STORE.get(user_id)

    if not stored_otp_info:
        return jsonify({"error": "No verification process started for this user."}), 404

    # Kiểm tra xem có đúng số điện thoại, đúng mã và chưa hết hạn không
    if (stored_otp_info['phone'] == phone_number and 
        stored_otp_info['code'] == code and 
        time.time() < stored_otp_info['expires_at']):
        
        # Xóa OTP đã dùng
        del OTP_STORE[user_id]
        
        # Lấy platform_id của Zalo từ cache hoặc hard-code
        platform_id_zalo = PLATFORM_IDS.get('zalo', 1) 
        # (Lấy tên người dùng Zalo, có thể cần một hàm mới trong ZaloApiClient)
        zalo_user_info = zalo_api_client.get_user_info(phone_number)
        zalo_username = zalo_user_info.name if zalo_user_info else "Zalo User"

        # Gọi hàm liên kết tài khoản
        return _link_platform_account(
            user_id,
            platform_id_zalo,
            "zalo",
            phone_number, # platform_user_id của Zalo là SĐT
            zalo_username
        )
    else:
        return jsonify({"error": "Invalid or expired verification code."}), 400


def run_web_app():
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_web_app()
