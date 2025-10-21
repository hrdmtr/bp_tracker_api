"""
血圧認識APIのテスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.models.response import BloodPressureData


class TestRecognitionAPI:
    """血圧認識APIのテスト"""

    def test_recognition_missing_uuid(self, client: TestClient):
        """UUIDなしでリクエストした場合"""
        response = client.post(
            "/api/v1/recognize-blood-pressure",
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_UUID"

    def test_recognition_invalid_uuid(self, client: TestClient):
        """無効なUUIDでリクエストした場合"""
        response = client.post(
            "/api/v1/recognize-blood-pressure",
            headers={"X-User-UUID": "invalid-uuid"},
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_UUID"

    def test_recognition_missing_image(self, client: TestClient, valid_uuid: str):
        """画像なしでリクエストした場合"""
        response = client.post(
            "/api/v1/recognize-blood-pressure",
            headers={"X-User-UUID": valid_uuid},
        )
        assert response.status_code == 422  # FastAPIのバリデーションエラー

    @patch("app.services.openai_service.OpenAIService.recognize_blood_pressure")
    @patch("app.database.supabase.SupabaseClient.get_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.increment_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.is_uuid_blocked")
    def test_recognition_success(
        self,
        mock_is_blocked,
        mock_increment,
        mock_get_count,
        mock_recognize,
        client: TestClient,
        valid_uuid: str,
    ):
        """正常な血圧認識"""
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

        response = client.post(
            "/api/v1/recognize-blood-pressure",
            headers={"X-User-UUID": valid_uuid},
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["systolic"] == 128
        assert data["data"]["diastolic"] == 82
        assert data["data"]["pulse"] == 72

    @patch("app.services.openai_service.OpenAIService.recognize_blood_pressure")
    @patch("app.database.supabase.SupabaseClient.get_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.increment_rate_limit_count")
    @patch("app.database.supabase.SupabaseClient.is_uuid_blocked")
    def test_recognition_failed(
        self,
        mock_is_blocked,
        mock_increment,
        mock_get_count,
        mock_recognize,
        client: TestClient,
        valid_uuid: str,
    ):
        """画像認識失敗"""
        # モック設定
        mock_is_blocked.return_value = False
        mock_get_count.return_value = {
            "count": 0,
            "reset_at": "2025-10-22T00:00:00+09:00",
        }
        mock_increment.return_value = True
        mock_recognize.return_value = (None, "NO_DISPLAY_DETECTED")

        response = client.post(
            "/api/v1/recognize-blood-pressure",
            headers={"X-User-UUID": valid_uuid},
            files={"image": ("test.jpg", b"fake image data", "image/jpeg")},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NO_DISPLAY_DETECTED"
