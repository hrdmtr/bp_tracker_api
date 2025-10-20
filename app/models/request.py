"""
リクエストモデル定義

- RecordMeasurementRequest
- RecognizeBloodPressureRequest
- WeatherRequest
"""

from datetime import datetime
from typing import Optional

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field


class RecognizeBloodPressureRequest(BaseModel):
    """血圧認識リクエスト"""

    image: UploadFile = Field(..., description="血圧計の画像ファイル")
    timestamp: Optional[str] = Field(None, description="測定日時（ISO 8601形式）")


class WeatherRequest(BaseModel):
    """天気情報取得リクエスト"""

    city: str = Field(..., description="都市名（例: 札幌市、東京都）")
    timestamp: Optional[str] = Field(None, description="測定日時（ISO 8601形式）")


class RecordMeasurementRequest(BaseModel):
    """統合測定記録リクエスト（血圧認識 + 天気情報）"""

    image: UploadFile = Field(..., description="血圧計の画像ファイル")
    city: str = Field(..., description="都市名（例: 札幌市、東京都）")
    timestamp: Optional[str] = Field(None, description="測定日時（ISO 8601形式）")
