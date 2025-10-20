"""
セキュリティ関連

- UUID形式検証
- レート制限ロジック（UUID単位、IP単位）
- 異常パターン検知
"""

import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Header, HTTPException, Request, status

from app.core.config import get_settings
from app.database.supabase import get_supabase_client
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def validate_uuid_format(uuid_string: str) -> bool:
    """
    UUID形式が正しいか検証

    Args:
        uuid_string: UUID文字列

    Returns:
        正しい形式の場合True
    """
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


async def verify_uuid(
    request: Request, x_user_uuid: str = Header(..., alias="X-User-UUID")
) -> str:
    """
    UUIDヘッダーを検証

    Args:
        request: FastAPIリクエスト
        x_user_uuid: X-User-UUIDヘッダー

    Returns:
        検証済みUUID

    Raises:
        HTTPException: UUIDが不正な場合
    """
    if not x_user_uuid:
        logger.warning("Missing X-User-UUID header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "MISSING_UUID",
                    "message": "X-User-UUID ヘッダーが必要です",
                },
            },
        )

    if not validate_uuid_format(x_user_uuid):
        logger.warning(f"Invalid UUID format: {x_user_uuid}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "INVALID_UUID",
                    "message": "UUIDの形式が不正です",
                },
            },
        )

    # ブラックリストチェック（フェーズ2以降）
    supabase = get_supabase_client()
    if await supabase.is_uuid_blocked(x_user_uuid):
        logger.warning(f"Blocked UUID attempted access: {x_user_uuid}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "UUID_BLOCKED",
                    "message": "このUUIDは永久ブロックされています",
                    "contact": "support@your-domain.com",
                },
            },
        )

    return x_user_uuid


async def check_rate_limit(uuid: str, endpoint: str, daily_limit: int) -> None:
    """
    レート制限をチェック

    Args:
        uuid: ユーザーUUID
        endpoint: エンドポイント名
        daily_limit: 日次制限数

    Raises:
        HTTPException: レート制限超過の場合
    """
    supabase = get_supabase_client()

    # 現在のカウントを取得
    rate_data = await supabase.get_rate_limit_count(uuid, endpoint)

    if rate_data:
        count = rate_data["count"]
        reset_at = rate_data["reset_at"]

        # 制限超過チェック
        if count >= daily_limit:
            logger.warning(f"Rate limit exceeded for UUID {uuid} on endpoint {endpoint}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"1日のリクエスト上限（{daily_limit}回）に達しました",
                        "retry_after": int((reset_at - datetime.now(reset_at.tzinfo)).total_seconds()),
                        "limit": daily_limit,
                        "remaining": 0,
                        "reset_at": reset_at.isoformat(),
                    },
                },
                headers={
                    "X-RateLimit-Limit": str(daily_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at.timestamp())),
                    "X-RateLimit-Reset-Human": reset_at.isoformat(),
                },
            )

    # カウントをインクリメント
    await supabase.increment_rate_limit_count(uuid, endpoint)

    # 残り回数を計算
    remaining = daily_limit - ((rate_data["count"] if rate_data else 0) + 1)
    logger.info(f"Rate limit check passed for UUID {uuid}: {remaining} remaining")
