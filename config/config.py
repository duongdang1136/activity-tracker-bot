from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Dict, Any
import json
import os
from dotenv import load_dotenv

PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(PROJECT_ROOT_DIR, '.env')
print(f"DEBUG: Đang cố gắng đọc file cấu hình từ: {ENV_FILE_PATH}")

if os.path.exists(ENV_FILE_PATH):
    print(f"DEBUG: Tìm thấy file .env tại '{ENV_FILE_PATH}'. Đang nạp biến...")
    # 2. Dùng load_dotenv để nạp các biến vào môi trường của Python
    load_dotenv(dotenv_path=ENV_FILE_PATH)
else:
    print(f"⚠️ CẢNH BÁO: Không tìm thấy file .env. Các biến sẽ được lấy từ hệ thống.")

class SupabaseConfig(BaseSettings):
    url: str = Field(..., alias='SUPABASE_URL')
    key: str = Field(..., alias='SUPABASE_KEY')
    
class ZaloConfig(BaseSettings):
    phone: str = Field(..., alias='ZALO_PHONE')
    password: str = Field(..., alias='ZALO_PASSWORD')
    imei: str = Field(..., alias='ZALO_IMEI')
    cookies: Dict[str, Any] = Field(default_factory=dict, alias='ZALO_COOKIES')
    
    @field_validator('cookies', mode='before')
    @classmethod
    def parse_cookies(cls, v: Any) -> Dict[str, Any]:
        """
        Tự động chuyển đổi chuỗi JSON từ .env thành dictionary.
        Nếu giá trị không phải chuỗi hoặc không hợp lệ, trả về dict rỗng.
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v if isinstance(v, dict) else {}
    
class DiscordConfig(BaseSettings):
    token: str = Field(..., alias='DISCORD_TOKEN')

class TelegramConfig(BaseSettings):
    token: str = Field(..., alias='TELEGRAM_TOKEN')    
    
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH, 
        env_file_encoding='utf-8', 
        extra='ignore',
        case_sensitive=True
    )
    supabase: SupabaseConfig = SupabaseConfig()
    zalo: ZaloConfig = ZaloConfig()
    discord: DiscordConfig = DiscordConfig()
    telegram: TelegramConfig = TelegramConfig()

settings = AppConfig()
