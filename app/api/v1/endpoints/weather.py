"""
天気情報取得API

GET /api/v1/weather
- 天気情報取得のみ
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.core.security import check_rate_limit, verify_uuid
from app.models.response import ErrorResponse, WeatherResponse
from app.services.weather_service import get_weather_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.get(
    "/weather",
    response_model=WeatherResponse,
    responses={
        200: {"description": "成功"},
        400: {"model": ErrorResponse, "description": "都市名が不正"},
        429: {"model": ErrorResponse, "description": "レート制限超過"},
        503: {"model": ErrorResponse, "description": "天気APIサービスが利用不可"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
    summary="天気情報取得API",
    description="都市名から天気情報を取得します。",
)
async def get_weather(
    city: str = Query(..., description="都市名（例: 札幌市、東京都）"),
    timestamp: str | None = Query(None, description="測定日時（ISO 8601形式）"),
    uuid: str = Depends(verify_uuid),
):
    """天気情報取得エンドポイント"""

    # レート制限チェック
    await check_rate_limit(uuid, "weather", settings.rate_limit_weather_daily)

    try:
        # 天気情報取得
        weather_service = get_weather_service()
        weather_data, weather_error = await weather_service.get_weather(city)

        if weather_error == "INVALID_CITY":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_CITY",
                        "message": f"都市名が不正または見つかりません: {city}",
                    },
                },
            )

        if weather_error == "WEATHER_API_UNAVAILABLE":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": {
                        "code": "WEATHER_API_UNAVAILABLE",
                        "message": "天気情報を取得できませんでした",
                        "details": "天気APIサービスが一時的に利用できません",
                    },
                },
            )

        # タイムスタンプ
        retrieved_at = timestamp or datetime.now(timezone.utc).isoformat()

        # レスポンス作成
        response = WeatherResponse(
            success=True, data=weather_data, retrieved_at=retrieved_at
        )

        logger.info(f"Successfully fetched weather for UUID {uuid}: {city}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_weather: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "サーバー内部エラーが発生しました",
                },
            },
        )
