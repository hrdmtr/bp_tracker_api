"""
レスポンスモデル定義

- BloodPressureData
- WeatherData
- ErrorResponse
- SuccessResponse
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class BloodPressureData(BaseModel):
    """血圧データ"""

    systolic: int = Field(..., description="最高血圧 (mmHg)")
    diastolic: int = Field(..., description="最低血圧 (mmHg)")
    pulse: int = Field(..., description="脈拍数 (拍/分)")
    device_model: Optional[str] = Field(None, description="血圧計の機種名・型番")


class WeatherData(BaseModel):
    """天気データ"""

    status: str = Field(..., description="取得ステータス（success / failed）")
    weather: Optional[str] = Field(None, description="天気の日本語表記")
    weather_code: Optional[str] = Field(None, description="天気コード")
    temperature: Optional[float] = Field(None, description="気温 (℃)")
    pressure: Optional[float] = Field(None, description="気圧 (hPa)")
    humidity: Optional[int] = Field(None, description="湿度 (%)")
    city: Optional[str] = Field(None, description="都市名")
    error_message: Optional[str] = Field(None, description="エラーメッセージ（失敗時）")


class RecognizeBloodPressureResponse(BaseModel):
    """血圧認識レスポンス"""

    success: bool = Field(..., description="成功フラグ")
    data: Optional[BloodPressureData] = Field(None, description="血圧データ")
    recognized_at: Optional[str] = Field(None, description="認識日時（ISO 8601形式）")


class WeatherResponse(BaseModel):
    """天気情報レスポンス"""

    success: bool = Field(..., description="成功フラグ")
    data: Optional[WeatherData] = Field(None, description="天気データ")
    retrieved_at: Optional[str] = Field(None, description="取得日時（ISO 8601形式）")


class RecordMeasurementData(BaseModel):
    """統合測定記録データ"""

    blood_pressure: BloodPressureData = Field(..., description="血圧データ")
    weather: WeatherData = Field(..., description="天気データ")
    timestamp: str = Field(..., description="測定日時（ISO 8601形式）")


class RecordMeasurementResponse(BaseModel):
    """統合測定記録レスポンス"""

    success: bool = Field(..., description="成功フラグ")
    data: Optional[RecordMeasurementData] = Field(None, description="測定データ")


class ErrorDetail(BaseModel):
    """エラー詳細"""

    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    details: Optional[str] = Field(None, description="詳細情報")
    suggestions: Optional[list[str]] = Field(None, description="解決方法の提案")
    retry_after: Optional[int] = Field(None, description="リトライ可能になるまでの秒数")
    limit: Optional[int] = Field(None, description="レート制限の上限")
    remaining: Optional[int] = Field(None, description="レート制限の残り")
    reset_at: Optional[str] = Field(None, description="レート制限リセット日時")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""

    success: bool = Field(False, description="成功フラグ（常にFalse）")
    error: ErrorDetail = Field(..., description="エラー詳細")


class HealthCheckResponse(BaseModel):
    """ヘルスチェックレスポンス"""

    status: str = Field(..., description="ステータス")
    version: str = Field(..., description="APIバージョン")
