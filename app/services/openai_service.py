"""
OpenAI API連携サービス

- 画像を受け取り、血圧値を抽出
- タイムアウト: 30秒
- エラーハンドリング
"""

import base64
from io import BytesIO
from typing import Optional

from openai import AsyncOpenAI, OpenAIError
from PIL import Image

from app.core.config import get_settings
from app.models.response import BloodPressureData
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OpenAIService:
    """OpenAI API連携サービス"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key, timeout=settings.openai_timeout
        )
        self.model = settings.openai_model

    async def recognize_blood_pressure(
        self, image_bytes: bytes
    ) -> tuple[Optional[BloodPressureData], Optional[str]]:
        """
        血圧計画像から測定値を抽出

        Args:
            image_bytes: 画像データ（バイト列）

        Returns:
            (BloodPressureData, None) if success
            (None, error_code) if failure
        """
        try:
            # 画像をbase64エンコード
            base64_image = base64.b64encode(image_bytes).decode("utf-8")

            # プロンプト
            prompt = """あなたは血圧計の画像を解析する専門システムです。
画像から以下の情報を正確に抽出してください：

1. 最高血圧（収縮期血圧）: mmHg単位の数値
2. 最低血圧（拡張期血圧）: mmHg単位の数値
3. 脈拍数: 拍/分単位の数値
4. 機種名・型番: メーカー名と型番（画像に表示されている場合のみ）

重要な注意事項：
- 数値のみを抽出してください（単位は含めない）
- 読み取れない項目はnullを返してください
- 血圧計が写っていない場合はエラーを返してください
- 画像がぼやけている場合でも、読み取れる範囲で抽出してください

以下のJSON形式で返してください：
{
  "systolic": number | null,
  "diastolic": number | null,
  "pulse": number | null,
  "device_model": string | null
}"""

            # OpenAI API呼び出し
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
            )

            # レスポンスをパース
            content = response.choices[0].message.content
            if not content:
                logger.error("OpenAI returned empty response")
                return None, "RECOGNITION_FAILED"

            # JSONパース
            import json

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response: {content}")
                return None, "RECOGNITION_FAILED"

            # 必須フィールドチェック
            if data.get("systolic") is None or data.get("diastolic") is None or data.get("pulse") is None:
                logger.warning("OpenAI could not extract required blood pressure values")
                return None, "NO_DISPLAY_DETECTED"

            # BloodPressureDataに変換
            bp_data = BloodPressureData(
                systolic=int(data["systolic"]),
                diastolic=int(data["diastolic"]),
                pulse=int(data["pulse"]),
                device_model=data.get("device_model"),
            )

            logger.info(f"Successfully recognized blood pressure: {bp_data.systolic}/{bp_data.diastolic}")
            return bp_data, None

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            return None, "RECOGNITION_FAILED"
        except Exception as e:
            logger.error(f"Unexpected error in recognize_blood_pressure: {e}", exc_info=True)
            return None, "RECOGNITION_FAILED"


# シングルトンインスタンス
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """OpenAIServiceのシングルトンインスタンスを取得"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
