"""
Supabase接続・クエリ

- レート制限カウンターテーブル操作
- フェーズ2以降: ブラックリスト操作
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from supabase import Client, create_client

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SupabaseClient:
    """Supabaseクライアント"""

    def __init__(self):
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)

    async def get_rate_limit_count(self, uuid: str, endpoint: str) -> Optional[dict]:
        """
        レート制限カウントを取得

        Args:
            uuid: ユーザーUUID
            endpoint: エンドポイント名

        Returns:
            {count: int, reset_at: datetime} or None
        """
        try:
            response = (
                self.client.table("rate_limit_counters")
                .select("*")
                .eq("uuid", uuid)
                .eq("endpoint", endpoint)
                .maybe_single()
                .execute()
            )

            if response.data:
                return {
                    "count": response.data["count"],
                    "reset_at": datetime.fromisoformat(response.data["reset_at"]),
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get rate limit count: {e}", exc_info=True)
            return None

    async def increment_rate_limit_count(self, uuid: str, endpoint: str) -> bool:
        """
        レート制限カウントをインクリメント

        Args:
            uuid: ユーザーUUID
            endpoint: エンドポイント名

        Returns:
            成功した場合True
        """
        try:
            now = datetime.now(timezone.utc)
            reset_at = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # 既存レコードを取得
            existing = await self.get_rate_limit_count(uuid, endpoint)

            if existing:
                # リセット時刻を過ぎている場合はカウントをリセット
                if existing["reset_at"] < now:
                    self.client.table("rate_limit_counters").update(
                        {"count": 1, "reset_at": reset_at.isoformat()}
                    ).eq("uuid", uuid).eq("endpoint", endpoint).execute()
                else:
                    # カウントをインクリメント
                    self.client.table("rate_limit_counters").update(
                        {"count": existing["count"] + 1}
                    ).eq("uuid", uuid).eq("endpoint", endpoint).execute()
            else:
                # 新規レコード作成
                self.client.table("rate_limit_counters").insert(
                    {"uuid": uuid, "endpoint": endpoint, "count": 1, "reset_at": reset_at.isoformat()}
                ).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to increment rate limit count: {e}", exc_info=True)
            return False

    async def is_uuid_blocked(self, uuid: str) -> bool:
        """
        UUIDがブラックリストに含まれるか確認（フェーズ2以降）

        Args:
            uuid: ユーザーUUID

        Returns:
            ブロックされている場合True
        """
        try:
            response = (
                self.client.table("blacklisted_uuids")
                .select("uuid")
                .eq("uuid", uuid)
                .maybe_single()
                .execute()
            )

            return response.data is not None

        except Exception as e:
            # テーブルが存在しない場合（フェーズ1）はFalseを返す
            logger.debug(f"Blacklist check failed (table may not exist): {e}")
            return False


# シングルトンインスタンス
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Supabaseクライアントのシングルトンインスタンスを取得"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
