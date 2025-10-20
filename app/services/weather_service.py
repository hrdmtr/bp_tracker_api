"""
OpenWeatherMap API連携サービス

- 都市名から天気情報取得
- 日本語翻訳（英語 → 日本語）
- タイムアウト: 10秒
"""

from typing import Optional

import httpx

from app.core.config import get_settings
from app.models.response import WeatherData
from app.utils.city_mapper import convert_city_to_english
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 天気コードの日本語変換テーブル
WEATHER_TRANSLATION = {
    "Clear": "晴れ",
    "Clouds": "曇り",
    "Rain": "雨",
    "Drizzle": "霧雨",
    "Thunderstorm": "雷雨",
    "Snow": "雪",
    "Mist": "霧",
    "Smoke": "煙霧",
    "Haze": "もや",
    "Dust": "砂塵",
    "Fog": "霧",
    "Sand": "砂嵐",
    "Ash": "火山灰",
    "Squall": "スコール",
    "Tornado": "竜巻",
}

# 天気コード変換
WEATHER_CODE_MAPPING = {
    "Clear": "clear",
    "Clouds": "cloudy",
    "Rain": "rain",
    "Drizzle": "rain",
    "Thunderstorm": "thunderstorm",
    "Snow": "snow",
    "Mist": "fog",
    "Smoke": "fog",
    "Haze": "fog",
    "Dust": "fog",
    "Fog": "fog",
    "Sand": "fog",
    "Ash": "fog",
    "Squall": "rain",
    "Tornado": "thunderstorm",
}


class WeatherService:
    """天気情報取得サービス"""

    def __init__(self):
        self.api_key = settings.openweathermap_api_key
        self.timeout = settings.openweathermap_timeout
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    async def get_weather(
        self, japanese_city: str
    ) -> tuple[Optional[WeatherData], Optional[str]]:
        """
        都市名から天気情報を取得

        Args:
            japanese_city: 日本語都市名（例: "札幌市"）

        Returns:
            (WeatherData, None) if success
            (WeatherData with status="failed", error_code) if API failed but graceful
            (None, error_code) if invalid city
        """
        try:
            # 都市名を英語に変換
            english_city = convert_city_to_english(japanese_city)
            if not english_city:
                logger.warning(f"Invalid city name: {japanese_city}")
                return None, "INVALID_CITY"

            # OpenWeatherMap API呼び出し
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": f"{english_city},JP",
                        "appid": self.api_key,
                        "units": "metric",
                        "lang": "ja",
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"OpenWeatherMap API returned {response.status_code}: {response.text}"
                    )
                    # グレースフルに失敗
                    return (
                        WeatherData(
                            status="failed",
                            error_message="天気APIが一時的に利用できません",
                        ),
                        "WEATHER_API_UNAVAILABLE",
                    )

                data = response.json()

                # 天気情報を抽出
                weather_main = data["weather"][0]["main"]
                weather_japanese = WEATHER_TRANSLATION.get(weather_main, weather_main)
                weather_code = WEATHER_CODE_MAPPING.get(weather_main, "unknown")

                weather_data = WeatherData(
                    status="success",
                    weather=weather_japanese,
                    weather_code=weather_code,
                    temperature=float(data["main"]["temp"]),
                    pressure=float(data["main"]["pressure"]),
                    humidity=int(data["main"]["humidity"]),
                    city=japanese_city,
                )

                logger.info(f"Successfully fetched weather for {japanese_city}: {weather_japanese}")
                return weather_data, None

        except httpx.TimeoutException:
            logger.error(f"Weather API timeout for city: {japanese_city}")
            return (
                WeatherData(
                    status="failed",
                    error_message="天気情報の取得がタイムアウトしました",
                ),
                "WEATHER_API_UNAVAILABLE",
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_weather: {e}", exc_info=True)
            return (
                WeatherData(
                    status="failed",
                    error_message="天気APIが一時的に利用できません",
                ),
                "WEATHER_API_UNAVAILABLE",
            )


# シングルトンインスタンス
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """WeatherServiceのシングルトンインスタンスを取得"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
