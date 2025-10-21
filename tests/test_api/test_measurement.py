"""
統合測定記録APIのテスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.models.response import BloodPressureData, WeatherData


class TestMeasurementAPI:
    """統合測定記録APIのテスト"""

    def test_measurement_missing_uuid(self, client: TestClient):
        """UUIDなしでリクエストした場合"""
        response = client.post(
            "/api/v1/record-measurement",
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
            data={"city": "東京都"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_UUID"

    def test_measurement_missing_city(self, client: TestClient, valid_uuid: str):
        """都市名なしでリクエストした場合"""
        response = client.post(
            "/api/v1/record-measurement",
            headers={"X-User-UUID": valid_uuid},
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
        )
        assert response.status_code == 422  # FastAPIのバリデーションエラー

    @patch("app.services.openai_service.OpenAIService.recognize_blood_pressure")
    @patch("app.services.weather_service.WeatherService.get_weather")
    @patch("app.database.supabase.SupabaseClient.get_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.increment_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.is_uuid_blocked")
    def test_measurement_success(
        self,
        mock_is_blocked,
        mock_increment,
        mock_get_count,
        mock_weather,
        mock_recognize,
        client: TestClient,
        valid_uuid: str,
    ):
        """正常な統合測定記録"""
        # モック設定
        mock_is_blocked.return_value = False
        mock_get_count.return_value = {
            "count": 0,
            "reset_at": "2025-10-22T00:00:00+09:00",
        }
        mock_increment.return_value = True
        mock_recognize.return_value = (
            BloodPressureData(
                systolic=128, diastolic=82, pulse=72, device_model="Panasonic EW-BU16"
            ),
            None,
        )
        mock_weather.return_value = (
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

        response = client.post(
            "/api/v1/record-measurement",
            headers={"X-User-UUID": valid_uuid},
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
            data={"city": "東京都"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["blood_pressure"]["systolic"] == 128
        assert data["data"]["weather"]["status"] == "success"
        assert data["data"]["weather"]["city"] == "東京都"

    @patch("app.services.openai_service.OpenAIService.recognize_blood_pressure")
    @patch("app.services.weather_service.WeatherService.get_weather")
    @patch("app.database.supabase.SupabaseClient.get_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.increment_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.is_uuid_blocked")
    def test_measurement_weather_failed_gracefully(
        self,
        mock_is_blocked,
        mock_increment,
        mock_get_count,
        mock_weather,
        mock_recognize,
        client: TestClient,
        valid_uuid: str,
    ):
        """天気API失敗でもグレースフルに成功"""
        # モック設定
        mock_is_blocked.return_value = False
        mock_get_count.return_value = {
            "count": 0,
            "reset_at": "2025-10-22T00:00:00+09:00",
        }
        mock_increment.return_value = True
        mock_recognize.return_value = (
            BloodPressureData(
                systolic=128, diastolic=82, pulse=72, device_model="Panasonic EW-BU16"
            ),
            None,
        )
        mock_weather.return_value = (
            WeatherData(
                status="failed",
                error_message="天気APIが一時的に利用できません",
            ),
            "WEATHER_API_UNAVAILABLE",
        )

        response = client.post(
            "/api/v1/record-measurement",
            headers={"X-User-UUID": valid_uuid},
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
            data={"city": "東京都"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["blood_pressure"]["systolic"] == 128
        assert data["data"]["weather"]["status"] == "failed"

    @patch("app.services.openai_service.OpenAIService.recognize_blood_pressure")
    @patch("app.database.supabase.SupabaseClient.get_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.increment_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.is_uuid_blocked")
    def test_measurement_recognition_failed(
        self,
        mock_is_blocked,
        mock_increment,
        mock_get_count,
        mock_recognize,
        client: TestClient,
        valid_uuid: str,
    ):
        """血圧認識失敗時は422エラー"""
        # モック設定
        mock_is_blocked.return_value = False
        mock_get_count.return_value = {
            "count": 0,
            "reset_at": "2025-10-22T00:00:00+09:00",
        }
        mock_increment.return_value = True
        mock_recognize.return_value = (None, "NO_DISPLAY_DETECTED")

        response = client.post(
            "/api/v1/record-measurement",
            headers={"X-User-UUID": valid_uuid},
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
            data={"city": "東京都"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NO_DISPLAY_DETECTED"
