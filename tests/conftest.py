"""
pytest設定・共通フィクスチャ
"""

import os
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# テスト用環境変数設定
os.environ["APP_ENV"] = "testing"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["OPENWEATHERMAP_API_KEY"] = "test-weather-key"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-supabase-key"

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """同期テストクライアント"""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """非同期テストクライアント"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_uuid() -> str:
    """有効なUUID"""
    return "12345678-1234-1234-1234-123456789012"


@pytest.fixture
def invalid_uuid() -> str:
    """無効なUUID"""
    return "invalid-uuid-format"


@pytest.fixture
def sample_cities() -> dict[str, str]:
    """サンプル都市名"""
    return {
        "valid": "東京都",
        "valid_english": "Tokyo",
        "invalid": "存在しない都市",
    }
