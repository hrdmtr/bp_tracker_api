"""
設定管理

- 環境変数読み込み（.env + Secret Manager）
- OpenAI/OpenWeatherMap APIキー
- Supabase接続情報
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    app_env: str = "development"
    app_name: str = "bp-tracker-api"
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # OpenAI API
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_timeout: int = 30

    # OpenWeatherMap API
    openweathermap_api_key: str
    openweathermap_timeout: int = 10

    # Supabase
    supabase_url: str
    supabase_key: str

    # Rate Limiting
    rate_limit_recognition_daily: int = 100
    rate_limit_weather_daily: int = 500
    rate_limit_ip_hourly: int = 1000

    # Image Upload
    max_image_size_mb: int = 10

    @property
    def allowed_origins_list(self) -> list[str]:
        """CORS許可オリジンをリスト形式で取得"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def max_image_size_bytes(self) -> int:
        """画像サイズ上限をバイト単位で取得"""
        return self.max_image_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """設定をシングルトンとして取得"""
    return Settings()
