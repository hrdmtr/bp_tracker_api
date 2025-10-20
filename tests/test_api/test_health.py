"""
ヘルスチェックAPIのテスト
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """ヘルスチェックAPIのテスト"""

    def test_root_endpoint(self, client: TestClient):
        """ルートエンドポイントのテスト"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_endpoint(self, client: TestClient):
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_response_structure(self, client: TestClient):
        """ヘルスチェックレスポンスの構造テスト"""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert "version" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
