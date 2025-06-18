from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class SupabaseConfig(BaseSettings):
    url: str = Field(..., env='SUPABASE_URL')
    key: str = Field(..., env='SUPABASE_KEY')

class BotConfig(BaseSettings):
    inactive_warn_days: int = Field(30, env='BOT_INACTIVE_WARN_DAYS')
    management_check_interval_hours: int = Field(24, env='BOT_MANAGEMENT_CHECK_INTERVAL_HOURS')
    discord_token: str = Field(..., env='DISCORD_TOKEN')

class ZaloConfig(BaseSettings):
    phone: str = Field(..., env='ZALO_PHONE')
    password: str = Field(..., env='ZALO_PASSWORD')

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    supabase: SupabaseConfig = SupabaseConfig()
    bot: BotConfig = BotConfig() # BotConfig chứa DISCORD_TOKEN
    zalo: ZaloConfig = ZaloConfig() # Thêm cấu hình Zalo
    
settings = AppConfig()
