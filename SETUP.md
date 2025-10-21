# セットアップガイド

このガイドでは、血圧トラッカーAPIのローカル開発環境とCloud Runへのデプロイ手順を説明します。

## 前提条件

- **uv**がインストール済み
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Python 3.11以上
- Supabaseプロジェクト
- OpenAI APIキー
- OpenWeatherMap APIキー
- Google Cloud CLIインストール済み（Cloud Runデプロイ時）

---

## ローカル開発環境のセットアップ

### 1. リポジトリクローン

```bash
git clone <repository-url>
cd bp_tracker_api
```

### 2. 依存関係インストール

```bash
uv sync
```

### 3. 環境変数設定

`.env.example`をコピーして`.env`を作成：

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の値を設定：

```bash
# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# OpenWeatherMap API
OPENWEATHERMAP_API_KEY=your-openweathermap-api-key-here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
```

### 4. Supabaseテーブル作成

**詳細な手順は[Supabaseセットアップガイド](docs/SUPABASE_SETUP.md)を参照してください。**

Supabaseのダッシュボードにアクセスして、`supabase_schema.sql`のSQLを実行：

```sql
-- 最低限必要なテーブル（フェーズ1）
CREATE TABLE IF NOT EXISTS rate_limit_counters (
    uuid VARCHAR(36) NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    reset_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (uuid, endpoint)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_reset_at ON rate_limit_counters(reset_at);
CREATE INDEX IF NOT EXISTS idx_rate_limit_uuid ON rate_limit_counters(uuid);
```

### 5. 開発サーバー起動

```bash
uv run uvicorn app.main:app --reload --port 8000
```

サーバーが起動したら、以下にアクセス：

- **APIドキュメント（Swagger UI）**: http://localhost:8000/docs
- **APIドキュメント（ReDoc）**: http://localhost:8000/redoc
- **ヘルスチェック**: http://localhost:8000/health

### 6. 動作確認

#### ヘルスチェック

```bash
curl http://localhost:8000/health
```

#### 統合API（画像認識 + 天気情報）

```bash
curl -X POST http://localhost:8000/api/v1/record-measurement \
  -H "X-User-UUID: 12345678-1234-1234-1234-123456789012" \
  -F "image=@test_image.jpg" \
  -F "city=東京都"
```

#### 血圧認識のみ

```bash
curl -X POST http://localhost:8000/api/v1/recognize-blood-pressure \
  -H "X-User-UUID: 12345678-1234-1234-1234-123456789012" \
  -F "image=@test_image.jpg"
```

#### 天気情報のみ

```bash
curl "http://localhost:8000/api/v1/weather?city=東京都" \
  -H "X-User-UUID: 12345678-1234-1234-1234-123456789012"
```

---

## Google Cloud Runへのデプロイ

### 1. Google Cloud認証

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Secret Managerに機密情報を保存

```bash
# OpenAI APIキー
echo -n "sk-your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# OpenWeatherMap APIキー
echo -n "your-openweathermap-api-key" | gcloud secrets create openweathermap-api-key --data-file=-

# Supabase URL
echo -n "https://your-project.supabase.co" | gcloud secrets create supabase-url --data-file=-

# Supabase Key
echo -n "your-supabase-anon-key" | gcloud secrets create supabase-key --data-file=-
```

### 3. Cloud Runデプロイ

```bash
gcloud run deploy bp-tracker-api \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --max-instances 10 \
  --set-secrets "\
OPENAI_API_KEY=openai-api-key:latest,\
OPENWEATHERMAP_API_KEY=openweathermap-api-key:latest,\
SUPABASE_URL=supabase-url:latest,\
SUPABASE_KEY=supabase-key:latest"
```

デプロイが完了すると、サービスURLが表示されます：
```
https://bp-tracker-api-xxxx-an.a.run.app
```

### 4. 本番環境の動作確認

```bash
# ヘルスチェック
curl https://your-service-url.run.app/health

# 統合API
curl -X POST https://your-service-url.run.app/api/v1/record-measurement \
  -H "X-User-UUID: 12345678-1234-1234-1234-123456789012" \
  -F "image=@test_image.jpg" \
  -F "city=東京都"
```

---

## テスト実行

### 全テスト実行

```bash
uv run pytest
```

### カバレッジ付きテスト

```bash
uv run pytest --cov=app --cov-report=html
```

カバレッジレポートは`htmlcov/index.html`で確認できます。

### 特定のテストのみ実行

```bash
uv run pytest tests/test_api/test_measurement.py
```

---

## トラブルシューティング

### 1. `MISSING_UUID`エラー

**原因**: `X-User-UUID`ヘッダーが不足しています。

**解決方法**: すべてのリクエストに`X-User-UUID`ヘッダーを含めてください。

```bash
curl -H "X-User-UUID: your-uuid-here" ...
```

### 2. `INVALID_CITY`エラー

**原因**: 都市名が変換テーブルにありません。

**解決方法**: 47都道府県庁所在地のいずれかを指定してください。
- 例: 札幌市、東京都、大阪市、福岡市など

### 3. `RATE_LIMIT_EXCEEDED`エラー

**原因**: 日次リクエスト制限を超過しました。

**解決方法**:
- 画像認識API: 100リクエスト/日/UUID
- 天気API: 500リクエスト/日/UUID
- 制限がリセットされるまで待つか、別のUUIDを使用してください（開発時のみ）

### 4. OpenAI API認識失敗

**原因**: 画像が不鮮明、血圧計が写っていない、または照明不足。

**解決方法**:
- 血圧計の画面全体が写るように撮影
- 明るい場所で撮影
- 画面の反射を避ける
- 画像サイズ: 最大10MB

### 5. Supabase接続エラー

**原因**: Supabaseの認証情報が不正、またはテーブルが作成されていません。

**解決方法**:
1. `SUPABASE_URL`と`SUPABASE_KEY`が正しいか確認
2. `supabase_schema.sql`のテーブルが作成されているか確認
3. Supabaseダッシュボードでテーブルを確認

---

## 次のステップ

1. **テスト作成**: `tests/`ディレクトリにテストを追加
2. **CI/CD設定**: GitHub Actionsなどで自動テスト・デプロイを設定
3. **モニタリング**: Cloud Loggingでログを確認
4. **フェーズ2実装**: ブラックリスト機能の追加

---

## サポート

問題が発生した場合:
- **技術サポート**: tech-support@your-domain.com
- **プライバシーに関する問い合わせ**: privacy@your-domain.com
- **APIドキュメント**: `/docs`エンドポイントを参照
