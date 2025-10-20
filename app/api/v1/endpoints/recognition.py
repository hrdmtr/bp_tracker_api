"""
血圧認識API

POST /api/v1/recognize-blood-pressure
- 画像認識のみ
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.security import check_rate_limit, verify_uuid
from app.models.response import ErrorResponse, RecognizeBloodPressureResponse
from app.services.openai_service import get_openai_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.post(
    "/recognize-blood-pressure",
    response_model=RecognizeBloodPressureResponse,
    responses={
        200: {"description": "成功"},
        400: {"model": ErrorResponse, "description": "リクエストが不正"},
        422: {"model": ErrorResponse, "description": "画像認識失敗"},
        429: {"model": ErrorResponse, "description": "レート制限超過"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
    summary="血圧認識API",
    description="血圧計の画像から測定値を抽出します。",
)
async def recognize_blood_pressure(
    image: Annotated[UploadFile, File(description="血圧計の画像ファイル")],
    timestamp: Annotated[str | None, Form(description="測定日時（ISO 8601形式）")] = None,
    uuid: str = Depends(verify_uuid),
):
    """血圧認識エンドポイント"""

    # レート制限チェック
    await check_rate_limit(
        uuid, "recognize-blood-pressure", settings.rate_limit_recognition_daily
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

        # タイムスタンプ
        recognized_at = timestamp or datetime.now(timezone.utc).isoformat()

        # レスポンス作成
        response = RecognizeBloodPressureResponse(
            success=True, data=bp_data, recognized_at=recognized_at
        )

        logger.info(
            f"Successfully recognized blood pressure for UUID {uuid}: "
            f"{bp_data.systolic}/{bp_data.diastolic}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in recognize_blood_pressure: {e}", exc_info=True)
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
