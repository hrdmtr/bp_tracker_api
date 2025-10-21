"""
設定管理のテスト
"""

import pytest

from app.core.config import get_settings


class TestConfig:
    """設定管理のテスト"""

    def test_get_settings(self):
        """設定の取得"""
        settings = get_settings()
        assert settings is not None
        assert settings.app_name == "bp-tracker-api"
        assert settings.app_env == "testing"

    def test_settings_singleton(self):
        """設定がシングルトンであることを確認"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_allowed_origins_list(self):
        """CORS許可オリジンリストの取得"""
        settings = get_settings()
        origins = settings.allowed_origins_list
        assert isinstance(origins, list)
        assert len(origins) > 0

    def test_max_image_size_bytes(self):
        """画像サイズ上限のバイト単位変換"""
        settings = get_settings()
        bytes_size = settings.max_image_size_bytes
        assert bytes_size == settings.max_image_size_mb * 1024 * 1024
