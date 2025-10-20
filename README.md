# Blood Pressure Tracker API

血圧記録アプリ用のバックエンドAPIサービス。画像認識（OpenAI API）と天気情報取得（OpenWeatherMap API）の中継機能を提供します。

**重要**: このAPIはデータ保存を一切行わず、外部APIへの代理リクエストのみを提供します（プライバシーファースト設計）。

## 技術スタック

- **フレームワーク**: Python FastAPI
- **インフラ**: Google Cloud Run
- **データベース**: Supabase PostgreSQL（レート制限カウンター、将来的にブラックリスト管理）
- **外部API**:
  - OpenAI API（gpt-4o / gpt-4o-mini）
  - OpenWeatherMap API
- **シークレット管理**: Google Cloud Secret Manager

## ディレクトリ構成

```
bp_tracker_api/
├── app/
│   ├── main.py                    # FastAPIアプリケーション本体
│   │                              # - CORS設定、ミドルウェア、ルーター登録
│   │                              # - リクエストID生成、構造化ログ
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/         # APIエンドポイント実装
│   │       │   ├── measurement.py # POST /api/v1/record-measurement
│   │       │   │                  # - 統合API（画像認識 + 天気情報）
│   │       │   │                  # - グレースフル・デグラデーション対応
│   │       │   ├── recognition.py # POST /api/v1/recognize-blood-pressure
│   │       │   │                  # - 画像認識のみ
│   │       │   └── weather.py     # GET /api/v1/weather
│   │       │                      # - 天気情報取得のみ
│   │       └── dependencies.py    # 依存性注入
│   │                              # - UUID検証、レート制限チェック
│   │
│   ├── core/
│   │   ├── config.py              # 設定管理
│   │   │                          # - 環境変数読み込み（.env + Secret Manager）
│   │   │                          # - OpenAI/OpenWeatherMap APIキー
│   │   │                          # - Supabase接続情報
│   │   └── security.py            # セキュリティ関連
│   │                              # - UUID形式検証
│   │                              # - レート制限ロジック（UUID単位、IP単位）
│   │                              # - 異常パターン検知
│   │
│   ├── models/
│   │   ├── request.py             # Pydanticリクエストモデル
│   │   │                          # - RecordMeasurementRequest
│   │   │                          # - RecognizeBloodPressureRequest
│   │   │                          # - WeatherRequest
│   │   └── response.py            # Pydanticレスポンスモデル
│   │                              # - BloodPressureData
│   │                              # - WeatherData
│   │                              # - ErrorResponse
│   │
│   ├── services/
│   │   ├── openai_service.py      # OpenAI API連携サービス
│   │   │                          # - 画像を受け取り、血圧値を抽出
│   │   │                          # - タイムアウト: 30秒
│   │   │                          # - エラーハンドリング
│   │   ├── weather_service.py     # OpenWeatherMap API連携サービス
│   │   │                          # - 都市名から天気情報取得
│   │   │                          # - 日本語翻訳（英語 → 日本語）
│   │   │                          # - タイムアウト: 10秒
│   │   └── rate_limiter.py        # レート制限サービス
│   │                              # - Supabaseと連携してカウント管理
│   │                              # - 日次リセット処理
│   │
│   ├── database/
│   │   └── supabase.py            # Supabase接続・クエリ
│   │                              # - レート制限カウンターテーブル操作
│   │                              # - フェーズ2以降: ブラックリスト操作
│   │
│   └── utils/
│       ├── city_mapper.py         # 都市名変換テーブル
│       │                          # - 日本語都市名 → 英語（47都道府県庁所在地）
│       │                          # - 例: "札幌市" → "Sapporo"
│       └── logger.py              # 構造化ログ設定
│                                  # - JSON形式ログ出力
│                                  # - request_id、uuid、endpoint、durationを記録
│                                  # - 個人情報（血圧値、都市名等）は記録しない
│
├── tests/                         # テストコード
│   ├── conftest.py                # pytest設定・フィクスチャ
│   ├── test_api/                  # APIエンドポイントテスト
│   │   ├── test_measurement.py
│   │   ├── test_recognition.py
│   │   └── test_weather.py
│   └── test_services/             # サービス層テスト
│       ├── test_openai_service.py
│       ├── test_weather_service.py
│       └── test_rate_limiter.py
│
├── docs/                          # ドキュメント
│   ├── RD.md                      # 要件定義書（全体構想）
│   └── API_spec.md                # API仕様書
│
├── .env.example                   # 環境変数テンプレート
├── .gitignore
├── Dockerfile                     # Cloud Run用Dockerイメージ
├── pyproject.toml                 # uv設定
├── uv.lock                        # uvロックファイル
├── CLAUDE.md                      # Claude Code用ガイド
├── QA.md                          # 仕様策定時のQ&A記録
└── README.md                      # このファイル
```

## 主要機能

### 1. 統合API（推奨）
- **エンドポイント**: `POST /api/v1/record-measurement`
- **機能**: 血圧計画像認識 + 天気情報取得を一度に実行
- **特徴**: 天気API失敗時も血圧データは返却（グレースフル・デグラデーション）

### 2. 画像認識API
- **エンドポイント**: `POST /api/v1/recognize-blood-pressure`
- **機能**: 血圧計画像から測定値を抽出

### 3. 天気情報API
- **エンドポイント**: `GET /api/v1/weather?city={city}`
- **機能**: 都市名から天気情報を取得

## 認証

すべてのリクエストに `X-User-UUID` ヘッダーが必要です。

```bash
curl -X POST https://your-api-domain.com/api/v1/record-measurement \
  -H "X-User-UUID: a3b2c1d4-e5f6-7890-abcd-ef1234567890" \
  -F "image=@blood_pressure_meter.jpg" \
  -F "city=札幌市"
```

### 認証フェーズ
- **フェーズ1（現在）**: ソフトUUID認証（事前登録不要）
- **フェーズ2（将来）**: ブラックリスト機能追加
- **フェーズ3（将来）**: UUID登録制（ホワイトリスト）

## レート制限

### UUID単位
- 画像認識API: 100リクエスト/日
- 天気API: 500リクエスト/日
- 統合API: 100リクエスト/日

### IPアドレス単位
- 1000リクエスト/時間

レスポンスヘッダーに残り回数を含めます：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1634745600
X-RateLimit-Reset-Human: 2025-10-21T00:00:00+09:00
```

## セットアップ

### 前提条件
- Python 3.11以上
- **uv**インストール済み（`curl -LsSf https://astral.sh/uv/install.sh | sh`）
- Google Cloud CLIインストール済み
- Supabaseプロジェクト作成済み
- OpenAI APIキー取得済み
- OpenWeatherMap APIキー取得済み

### ローカル開発環境

1. **リポジトリクローン**
   ```bash
   git clone https://github.com/your-username/bp_tracker_api.git
   cd bp_tracker_api
   ```

2. **依存関係インストール**
   ```bash
   uv sync
   ```

4. **環境変数設定**
   ```bash
   cp .env.example .env
   # .envファイルを編集して必要な値を設定
   ```

5. **Supabaseテーブル作成**
   ```sql
   -- レート制限カウンターテーブル
   CREATE TABLE rate_limit_counters (
     uuid VARCHAR(36) NOT NULL,
     endpoint VARCHAR(100) NOT NULL,
     count INTEGER NOT NULL DEFAULT 0,
     reset_at TIMESTAMP NOT NULL,
     PRIMARY KEY (uuid, endpoint)
   );

   CREATE INDEX idx_reset_at ON rate_limit_counters(reset_at);
   ```

6. **開発サーバー起動**
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

7. **APIドキュメント確認**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### テスト実行

```bash
# 全テスト実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=app --cov-report=html

# 特定のテストのみ
uv run pytest tests/test_api/test_measurement.py
```

## デプロイ（Google Cloud Run）

### 1. Secret Manager設定

```bash
# OpenAI APIキー
gcloud secrets create openai-api-key --data-file=-
# プロンプトでAPIキーを入力

# OpenWeatherMap APIキー
gcloud secrets create openweathermap-api-key --data-file=-

# Supabase接続情報
gcloud secrets create supabase-url --data-file=-
gcloud secrets create supabase-key --data-file=-
```

### 2. Cloud Runデプロイ

```bash
# イメージビルド&デプロイ
gcloud run deploy bp-tracker-api \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-secrets "OPENAI_API_KEY=openai-api-key:latest,OPENWEATHERMAP_API_KEY=openweathermap-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest"
```

### 3. 動作確認

```bash
# ヘルスチェック
curl https://your-service-url.run.app/health

# 統合API テスト
curl -X POST https://your-service-url.run.app/api/v1/record-measurement \
  -H "X-User-UUID: test-uuid" \
  -F "image=@test_image.jpg" \
  -F "city=東京都"
```

## セキュリティ

### データ保存ポリシー
- **画像**: メモリ上で処理、認識後即座に削除
- **血圧測定値**: サーバーに保存しない（レスポンス返却後破棄）
- **位置情報**: 都市名のみ受け取り、処理後破棄

### ログポリシー
- **記録する**: タイムスタンプ、エンドポイント、HTTPステータス、UUID、request_id
- **記録しない**: 血圧値、機種名、都市名、その他個人情報
- **保持期間**: 30日

### HTTPS必須
すべてのエンドポイントはHTTPS（TLS 1.2以上）経由でのみアクセス可能。

## トラブルシューティング

### OpenAI APIタイムアウト
- タイムアウト設定: 30秒
- エラー時はユーザーに再撮影を促す（リトライなし）

### 天気API失敗
- 統合APIではグレースフルに失敗（血圧データは返却）
- `weather.status: "failed"` で通知

### レート制限超過
- ステータスコード: `429 Too Many Requests`
- レスポンスに `retry_after` と `reset_at` を含める

## ドキュメント

- **API仕様書**: [API_spec.md](./API_spec.md)
- **要件定義書**: [docs/RD.md](./docs/RD.md)
- **Q&A記録**: [QA.md](./QA.md)
- **Claude Code用ガイド**: [CLAUDE.md](./CLAUDE.md)

## ライセンス

(TBD)

## サポート

- **技術サポート**: tech-support@your-domain.com
- **プライバシーに関する問い合わせ**: privacy@your-domain.com
