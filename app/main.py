"""
FastAPIメインアプリケーション

- CORS設定
- ミドルウェア
- ルーター登録
- リクエストID生成
- 構造化ログ
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints import measurement, recognition, weather
from app.core.config import get_settings
from app.models.response import HealthCheckResponse
from app.utils.logger import get_logger, setup_logger

settings = get_settings()

# ロガー設定
setup_logger(level=settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル"""
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    yield
    logger.info(f"Shutting down {settings.app_name}")


# FastAPIアプリケーション
app = FastAPI(
    title="Blood Pressure Tracker API",
    description="Privacy-first proxy service for blood pressure image recognition and weather data",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    """リクエストID付与とログ記録ミドルウェア"""
    # リクエストID生成
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # リクエスト開始時刻
    start_time = time.time()

    # ログ記録用の追加情報
    log_extra = {
        "request_id": request_id,
        "method": request.method,
        "endpoint": request.url.path,
    }

    logger.info(f"Request started: {request.method} {request.url.path}", extra=log_extra)

    try:
        # リクエスト処理
        response = await call_next(request)

        # 処理時間計算
        duration = int((time.time() - start_time) * 1000)  # ミリ秒

        # レスポンスヘッダーにリクエストIDを追加
        response.headers["X-Request-ID"] = request_id

        # ログ記録
        log_extra["status_code"] = response.status_code
        log_extra["duration"] = duration
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- {response.status_code} ({duration}ms)",
            extra=log_extra,
        )

        return response

    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        log_extra["duration"] = duration
        logger.error(
            f"Request failed: {request.method} {request.url.path} ({duration}ms)",
            exc_info=True,
            extra=log_extra,
        )
        raise


# ルーター登録
app.include_router(measurement.router, prefix="/api/v1", tags=["Measurement"])
app.include_router(recognition.router, prefix="/api/v1", tags=["Recognition"])
app.include_router(weather.router, prefix="/api/v1", tags=["Weather"])


@app.get("/", response_model=HealthCheckResponse)
async def root():
    """ルートエンドポイント"""
    return HealthCheckResponse(status="ok", version="0.1.0")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
    return HealthCheckResponse(status="ok", version="0.1.0")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """グローバル例外ハンドラー"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": request_id, "endpoint": request.url.path},
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "サーバー内部エラーが発生しました",
            },
        },
        headers={"X-Request-ID": request_id},
    )
