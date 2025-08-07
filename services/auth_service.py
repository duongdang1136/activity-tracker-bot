import hashlib
import hmac
import time
import json
from urllib.parse import unquote
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from config.telegram_config import TELEGRAM_CONFIG
from services.user_service import UserService

class TelegramAuthService:
    def __init__(self):
        self.user_service = UserService()
        
    def verify_telegram_auth(self, auth_data):
        """
        Xác minh dữ liệu đăng nhập Telegram theo Telegram Login Widget
        https://core.telegram.org/widgets/login
        """
        try:
            # Extract hash from auth_data
            received_hash = auth_data.pop('hash', None)
            if not received_hash:
                return False, "Missing hash"
            
            # Check auth_date (không quá 24h)
            auth_date = auth_data.get('auth_date')
            if not auth_date:
                return False, "Missing auth_date"
                
            current_time = int(time.time())
            if current_time - int(auth_date) > TELEGRAM_CONFIG.AUTH_TIMEOUT:
                return False, "Auth data too old"
            
            # Tạo data string để verify
            data_check_string = '\n'.join([
                f"{key}={value}" 
                for key, value in sorted(auth_data.items())
            ])
            
            # Tạo secret key từ bot token
            secret_key = hashlib.sha256(TELEGRAM_CONFIG.BOT_TOKEN.encode()).digest()
            
            # Verify hash
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if calculated_hash != received_hash:
                return False, "Invalid hash"
                
            return True, "Valid"
            
        except Exception as e:
            return False, f"Verification error: {str(e)}"
    
    def link_telegram_account(self, hub_user_id, telegram_auth_data):
        """
        Liên kết tài khoản Hub với Telegram sau khi verify thành công
        """
        try:
            # Verify auth data
            is_valid, message = self.verify_telegram_auth(telegram_auth_data)
            if not is_valid:
                return False, message
            
            # Extract user info
            telegram_user = {
                'telegram_id': telegram_auth_data.get('id'),
                'first_name': telegram_auth_data.get('first_name', ''),
                'last_name': telegram_auth_data.get('last_name', ''),
                'username': telegram_auth_data.get('username', ''),
                'photo_url': telegram_auth_data.get('photo_url', ''),
                'auth_date': telegram_auth_data.get('auth_date')
            }
            
            # Check if Telegram account already linked
            existing_link = self.user_service.get_user_by_platform_id(
                'telegram', 
                str(telegram_user['telegram_id'])
            )
            
            if existing_link and existing_link['hub_user_id'] != hub_user_id:
                return False, "Telegram account already linked to another user"
            
            # Link accounts
            result = self.user_service.link_platform_account(
                hub_user_id=hub_user_id,
                platform='telegram',
                platform_user_id=str(telegram_user['telegram_id']),
                platform_data=telegram_user
            )
            
            if result:
                return True, "Account linked successfully"
            else:
                return False, "Failed to link account"
                
        except Exception as e:
            return False, f"Link error: {str(e)}"
    
    def unlink_telegram_account(self, hub_user_id):
        """Hủy liên kết tài khoản Telegram"""
        try:
            result = self.user_service.unlink_platform_account(
                hub_user_id=hub_user_id,
                platform='telegram'
            )
            return result, "Account unlinked" if result else "Failed to unlink"
        except Exception as e:
            return False, f"Unlink error: {str(e)}"
    
    def get_telegram_user_by_hub_id(self, hub_user_id):
        """Lấy thông tin Telegram user từ Hub user ID"""
        try:
            return self.user_service.get_platform_account(
                hub_user_id=hub_user_id,
                platform='telegram'
            )
        except Exception as e:
            return None

# Auth service instance
telegram_auth_service = TelegramAuthService()