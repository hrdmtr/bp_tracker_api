"""
セキュリティ関連のテスト
"""

import pytest

from app.core.security import validate_uuid_format


class TestSecurity:
    """セキュリティ関連のテスト"""

    @pytest.mark.parametrize(
        "uuid_string",
        [
            "12345678-1234-1234-1234-123456789012",
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "00000000-0000-0000-0000-000000000000",
            "ffffffff-ffff-ffff-ffff-ffffffffffff",
        ],
    )
    def test_valid_uuid_format(self, uuid_string: str):
        """有効なUUID形式のテスト"""
        assert validate_uuid_format(uuid_string) is True

    @pytest.mark.parametrize(
        "invalid_uuid",
        [
            "invalid-uuid",
            "12345678",
            "12345678-1234-1234-1234",  # 短い
            "12345678-1234-1234-1234-123456789012-extra",  # 長い
            "",
            "not-a-uuid-at-all",
            "12345678_1234_1234_1234_123456789012",  # ハイフンではなくアンダースコア
        ],
    )
    def test_invalid_uuid_format(self, invalid_uuid: str):
        """無効なUUID形式のテスト"""
        assert validate_uuid_format(invalid_uuid) is False
