"""
天気APIのテスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.models.response import WeatherData


class TestWeatherAPI:
    """天気APIのテスト"""

    def test_weather_missing_uuid(self, client: TestClient):
        """UUIDなしでリクエストした場合"""
        response = client.get("/api/v1/weather?city=東京都")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_UUID"

    def test_weather_invalid_uuid(self, client: TestClient):
        """無効なUUIDでリクエストした場合"""
        response = client.get(
            "/api/v1/weather?city=東京都",
            headers={"X-User-UUID": "invalid-uuid"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_UUID"

    def test_weather_missing_city(self, client: TestClient, valid_uuid: str):
        """都市名なしでリクエストした場合"""
        response = client.get(
            "/api/v1/weather",
            headers={"X-User-UUID": valid_uuid},
        )
        assert response.status_code == 422  # FastAPIのバリデーションエラー

    @patch("app.services.weather_service.WeatherService.get_weather")
    @patch("app.database.supabase.SupabaseClient.get_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.increment_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.is_uuid_blocked")
    def test_weather_success(
        self,
        mock_is_blocked,
        mock_increment,
        mock_get_count,
        mock_get_weather,
        client: TestClient,
        valid_uuid: str,
    ):
        """正常な天気情報取得"""
        # モック設定
        mock_is_blocked.return_value = False
        mock_get_count.return_value = {"count": 0, "reset_at": "2025-10-22T00:00:00+09:00"}
        mock_increment.return_value = True
        mock_get_weather.return_value = (
            WeatherData(
                status="success",
                weather="晴れ",
                weather_code="clear",
                temperature=23.5,
                pressure=1013.2,
                humidity=60,
                city="東京都",
            ),
            None,
        )

        response = client.get(
            "/api/v1/weather?city=東京都",
            headers={"X-User-UUID": valid_uuid},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "success"
        assert data["data"]["city"] == "東京都"
        assert data["data"]["weather"] == "晴れ"

    @patch("app.services.weather_service.WeatherService.get_weather")
    @patch("app.database.supabase.SupabaseClient.get_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.increment_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.is_uuid_blocked")
    def test_weather_invalid_city(
        self,
        mock_is_blocked,
        mock_increment,
        mock_get_count,
        mock_get_weather,
        client: TestClient,
        valid_uuid: str,
    ):
        """無効な都市名でリクエストした場合"""
        # モック設定
        mock_is_blocked.return_value = False
        mock_get_count.return_value = {"count": 0, "reset_at": "2025-10-22T00:00:00+09:00"}
        mock_increment.return_value = True
        mock_get_weather.return_value = (None, "INVALID_CITY")

        response = client.get(
            "/api/v1/weather?city=存在しない都市",
            headers={"X-User-UUID": valid_uuid},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CITY"
