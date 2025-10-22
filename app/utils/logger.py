"""
構造化ログ設定

- JSON形式でログ出力
- request_id、uuid、endpoint、durationを記録
- 個人情報（血圧値、都市名等）は記録しない
"""

import logging
import sys
from typing import Any

import json_log_formatter


class CustomJSONFormatter(json_log_formatter.JSONFormatter):
    """カスタムJSON形式ログフォーマッター"""

    def json_record(
        self, message: str, extra: dict[str, Any], record: logging.LogRecord
    ) -> dict[str, Any]:
        """ログレコードをJSON形式に変換"""
        from datetime import datetime, timezone

        json_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": message,
            "logger": record.name,
        }

        # request_id, uuid, endpoint, durationなどを追加
        if hasattr(record, "request_id"):
            json_record["request_id"] = record.request_id
        if hasattr(record, "uuid"):
            json_record["uuid"] = record.uuid
        if hasattr(record, "endpoint"):
            json_record["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            json_record["method"] = record.method
        if hasattr(record, "status_code"):
            json_record["status_code"] = record.status_code
        if hasattr(record, "duration"):
            json_record["duration_ms"] = record.duration

        # エラー情報
        if record.exc_info:
            json_record["exception"] = self.formatException(record.exc_info)

        # extra情報を追加（個人情報は含めないこと）
        if extra:
            json_record.update(extra)

        return json_record


def setup_logger(level: str = "INFO") -> logging.Logger:
    """ロガーをセットアップ"""
    # ルートロガー取得
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # 既存のハンドラーをクリア
    logger.handlers.clear()

    # JSONフォーマッター設定
    formatter = CustomJSONFormatter()

    # コンソールハンドラー追加
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """名前付きロガーを取得"""
    return logging.getLogger(name)
