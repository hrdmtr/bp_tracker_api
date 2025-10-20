"""
都市名変換テーブル

日本語都市名 → 英語（47都道府県庁所在地）
例: "札幌市" → "Sapporo"
"""

from typing import Optional

# 47都道府県庁所在地の日本語→英語変換テーブル
CITY_MAPPING: dict[str, str] = {
    # 北海道
    "札幌市": "Sapporo",
    "札幌": "Sapporo",
    # 東北
    "青森市": "Aomori",
    "青森": "Aomori",
    "盛岡市": "Morioka",
    "盛岡": "Morioka",
    "仙台市": "Sendai",
    "仙台": "Sendai",
    "秋田市": "Akita",
    "秋田": "Akita",
    "山形市": "Yamagata",
    "山形": "Yamagata",
    "福島市": "Fukushima",
    "福島": "Fukushima",
    # 関東
    "水戸市": "Mito",
    "水戸": "Mito",
    "宇都宮市": "Utsunomiya",
    "宇都宮": "Utsunomiya",
    "前橋市": "Maebashi",
    "前橋": "Maebashi",
    "さいたま市": "Saitama",
    "さいたま": "Saitama",
    "千葉市": "Chiba",
    "千葉": "Chiba",
    "東京都": "Tokyo",
    "東京": "Tokyo",
    "横浜市": "Yokohama",
    "横浜": "Yokohama",
    # 中部
    "新潟市": "Niigata",
    "新潟": "Niigata",
    "富山市": "Toyama",
    "富山": "Toyama",
    "金沢市": "Kanazawa",
    "金沢": "Kanazawa",
    "福井市": "Fukui",
    "福井": "Fukui",
    "甲府市": "Kofu",
    "甲府": "Kofu",
    "長野市": "Nagano",
    "長野": "Nagano",
    "岐阜市": "Gifu",
    "岐阜": "Gifu",
    "静岡市": "Shizuoka",
    "静岡": "Shizuoka",
    "名古屋市": "Nagoya",
    "名古屋": "Nagoya",
    # 近畿
    "津市": "Tsu",
    "津": "Tsu",
    "大津市": "Otsu",
    "大津": "Otsu",
    "京都市": "Kyoto",
    "京都": "Kyoto",
    "大阪市": "Osaka",
    "大阪": "Osaka",
    "神戸市": "Kobe",
    "神戸": "Kobe",
    "奈良市": "Nara",
    "奈良": "Nara",
    "和歌山市": "Wakayama",
    "和歌山": "Wakayama",
    # 中国
    "鳥取市": "Tottori",
    "鳥取": "Tottori",
    "松江市": "Matsue",
    "松江": "Matsue",
    "岡山市": "Okayama",
    "岡山": "Okayama",
    "広島市": "Hiroshima",
    "広島": "Hiroshima",
    "山口市": "Yamaguchi",
    "山口": "Yamaguchi",
    # 四国
    "徳島市": "Tokushima",
    "徳島": "Tokushima",
    "高松市": "Takamatsu",
    "高松": "Takamatsu",
    "松山市": "Matsuyama",
    "松山": "Matsuyama",
    "高知市": "Kochi",
    "高知": "Kochi",
    # 九州・沖縄
    "福岡市": "Fukuoka",
    "福岡": "Fukuoka",
    "佐賀市": "Saga",
    "佐賀": "Saga",
    "長崎市": "Nagasaki",
    "長崎": "Nagasaki",
    "熊本市": "Kumamoto",
    "熊本": "Kumamoto",
    "大分市": "Oita",
    "大分": "Oita",
    "宮崎市": "Miyazaki",
    "宮崎": "Miyazaki",
    "鹿児島市": "Kagoshima",
    "鹿児島": "Kagoshima",
    "那覇市": "Naha",
    "那覇": "Naha",
}


def convert_city_to_english(japanese_city: str) -> Optional[str]:
    """
    日本語都市名を英語に変換

    Args:
        japanese_city: 日本語都市名（例: "札幌市", "東京都"）

    Returns:
        英語都市名（例: "Sapporo", "Tokyo"）
        変換テーブルにない場合はNone
    """
    return CITY_MAPPING.get(japanese_city)


def is_valid_city(japanese_city: str) -> bool:
    """
    都市名が変換テーブルに存在するか確認

    Args:
        japanese_city: 日本語都市名

    Returns:
        変換テーブルに存在する場合True
    """
    return japanese_city in CITY_MAPPING


def get_supported_cities() -> list[str]:
    """
    サポートしている都市名一覧を取得

    Returns:
        日本語都市名のリスト
    """
    return list(CITY_MAPPING.keys())
