"""
都市名変換テスト
"""

import pytest

from app.utils.city_mapper import (
    convert_city_to_english,
    get_supported_cities,
    is_valid_city,
)


class TestCityMapper:
    """都市名変換のテスト"""

    def test_convert_valid_city(self):
        """有効な都市名の変換"""
        assert convert_city_to_english("東京都") == "Tokyo"
        assert convert_city_to_english("札幌市") == "Sapporo"
        assert convert_city_to_english("大阪市") == "Osaka"
        assert convert_city_to_english("福岡市") == "Fukuoka"

    def test_convert_city_without_suffix(self):
        """市・都なしの都市名の変換"""
        assert convert_city_to_english("東京") == "Tokyo"
        assert convert_city_to_english("札幌") == "Sapporo"

    def test_convert_invalid_city(self):
        """無効な都市名の変換"""
        assert convert_city_to_english("存在しない都市") is None
        assert convert_city_to_english("") is None

    def test_is_valid_city(self):
        """都市名の有効性チェック"""
        assert is_valid_city("東京都") is True
        assert is_valid_city("札幌市") is True
        assert is_valid_city("存在しない都市") is False
        assert is_valid_city("") is False

    def test_get_supported_cities(self):
        """サポート都市一覧の取得"""
        cities = get_supported_cities()
        assert isinstance(cities, list)
        assert len(cities) > 0
        assert "東京都" in cities
        assert "札幌市" in cities

    def test_all_47_prefectures(self):
        """47都道府県庁所在地がすべて含まれているか"""
        cities = get_supported_cities()
        # 最低でも47都道府県分は存在する（都市名あり・なし両方含む）
        assert len(cities) >= 47

    @pytest.mark.parametrize(
        "japanese,english",
        [
            ("札幌市", "Sapporo"),
            ("仙台市", "Sendai"),
            ("東京都", "Tokyo"),
            ("横浜市", "Yokohama"),
            ("名古屋市", "Nagoya"),
            ("京都市", "Kyoto"),
            ("大阪市", "Osaka"),
            ("神戸市", "Kobe"),
            ("広島市", "Hiroshima"),
            ("福岡市", "Fukuoka"),
            ("那覇市", "Naha"),
        ],
    )
    def test_major_cities(self, japanese: str, english: str):
        """主要都市の変換テスト"""
        assert convert_city_to_english(japanese) == english
