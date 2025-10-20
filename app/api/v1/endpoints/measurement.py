"""
統合測定記録API

POST /api/v1/record-measurement
- 血圧認識 + 天気情報取得を一度に実行
- グレースフル・デグラデーション対応
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.security import check_rate_limit, verify_uuid
from app.models.response import (
    ErrorResponse,
    RecordMeasurementData,
    RecordMeasurementResponse,
)
from app.services.openai_service import get_openai_service
from app.services.weather_service import get_weather_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.post(
    "/record-measurement",
    response_model=RecordMeasurementResponse,
    responses={
        200: {"description": "成功（天気取得失敗でも血圧認識成功なら200）"},
        400: {"model": ErrorResponse, "description": "リクエストが不正"},
        422: {"model": ErrorResponse, "description": "画像認識失敗"},
        429: {"model": ErrorResponse, "description": "レート制限超過"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
    summary="統合測定記録API（推奨）",
    description="血圧計画像認識と天気情報取得を一度に実行します。天気API失敗時も血圧データは返却されます。",
)
async def record_measurement(
    image: Annotated[UploadFile, File(description="血圧計の画像ファイル")],
    city: Annotated[str, Form(description="都市名（例: 札幌市、東京都）")],
    timestamp: Annotated[str | None, Form(description="測定日時（ISO 8601形式）")] = None,
    uuid: str = Depends(verify_uuid),
):
    """統合測定記録エンドポイント"""

    # レート制限チェック
    await check_rate_limit(
        uuid, "record-measurement", settings.rate_limit_recognition_daily
    )

    try:
        # 画像サイズチェック
        image_bytes = await image.read()
        if len(image_bytes) > settings.max_image_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "IMAGE_TOO_LARGE",
                        "message": f"画像サイズが大きすぎます（上限: {settings.max_image_size_mb}MB）",
                    },
                },
            )

        # 画像認識
        openai_service = get_openai_service()
        bp_data, bp_error = await openai_service.recognize_blood_pressure(image_bytes)

        if bp_error or bp_data is None:
            error_messages = {
                "NO_DISPLAY_DETECTED": "血圧計の画面が検出できませんでした",
                "RECOGNITION_FAILED": "血圧計の画像を認識できませんでした",
            }
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "success": False,
                    "error": {
                        "code": bp_error or "RECOGNITION_FAILED",
                        "message": error_messages.get(
                            bp_error or "RECOGNITION_FAILED",
                            "画像認識に失敗しました",
                        ),
                        "suggestions": [
                            "血圧計の画面全体が写るように撮影してください",
                            "明るい場所で撮影してください",
                            "画面に反射がないか確認してください",
                        ],
                    },
                },
            )

        # 天気情報取得（グレースフルに失敗）
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

        # タイムスタンプ
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()

        # レスポンス作成
        response = RecordMeasurementResponse(
            success=True,
            data=RecordMeasurementData(
                blood_pressure=bp_data, weather=weather_data, timestamp=timestamp
            ),
        )

        logger.info(
            f"Successfully recorded measurement for UUID {uuid}: "
            f"BP={bp_data.systolic}/{bp_data.diastolic}, "
            f"Weather={weather_data.status}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in record_measurement: {e}", exc_info=True)
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
