# Supabaseセットアップガイド

このガイドでは、血圧トラッカーAPIで使用するSupabaseプロジェクトのセットアップ手順を説明します。

## 目次

1. [Supabaseプロジェクト作成](#1-supabaseプロジェクト作成)
2. [データベーステーブル作成](#2-データベーステーブル作成)
3. [APIキー取得](#3-apiキー取得)
4. [Row Level Security (RLS) 設定](#4-row-level-security-rls-設定)
5. [動作確認](#5-動作確認)
6. [トラブルシューティング](#6-トラブルシューティング)

---

## 1. Supabaseプロジェクト作成

### 1.1 Supabaseアカウント作成

1. [Supabase](https://supabase.com/)にアクセス
2. 「Start your project」をクリック
3. GitHubアカウントでサインアップ（推奨）

### 1.2 新規プロジェクト作成

1. ダッシュボードで「New Project」をクリック
2. プロジェクト情報を入力：
   - **Name**: `bp-tracker` (任意の名前)
   - **Database Password**: 強力なパスワードを生成（後で使用）
   - **Region**: `Northeast Asia (Tokyo)` (推奨：レイテンシー低減のため)
   - **Pricing Plan**: `Free` (開発用) または `Pro` (本番用)
3. 「Create new project」をクリック
4. プロジェクト作成完了まで1-2分待機

---

## 2. データベーステーブル作成

### 2.1 SQL Editorを開く

1. 左サイドバーから「SQL Editor」をクリック
2. 「New query」をクリック

### 2.2 フェーズ1テーブル作成（必須）

以下のSQLを実行して、レート制限用テーブルを作成します：

```sql
-- レート制限カウンターテーブル
CREATE TABLE IF NOT EXISTS rate_limit_counters (
    uuid VARCHAR(36) NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    reset_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (uuid, endpoint)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_rate_limit_reset_at ON rate_limit_counters(reset_at);
CREATE INDEX IF NOT EXISTS idx_rate_limit_uuid ON rate_limit_counters(uuid);

-- コメント追加
COMMENT ON TABLE rate_limit_counters IS 'レート制限カウンター（UUID単位）';
COMMENT ON COLUMN rate_limit_counters.uuid IS 'ユーザーUUID';
COMMENT ON COLUMN rate_limit_counters.endpoint IS 'エンドポイント名';
COMMENT ON COLUMN rate_limit_counters.count IS 'リクエストカウント';
COMMENT ON COLUMN rate_limit_counters.reset_at IS 'リセット日時（日次）';
```

### 2.3 テーブル作成確認

1. 左サイドバーから「Table Editor」をクリック
2. `rate_limit_counters`テーブルが表示されることを確認

---

## 3. APIキー取得

### 3.1 プロジェクト設定を開く

1. 左サイドバーから「Settings」（歯車アイコン）をクリック
2. 「API」をクリック

### 3.2 必要な情報をコピー

以下の情報を`.env`ファイル用にコピーします：

#### Project URL
```
URL: https://xxxxxxxxxxx.supabase.co
```

#### Project API keys

- **anon public**: クライアント側で使用（今回は使用しない）
- **service_role**: サーバー側で使用（**これを使用**）

**重要**: `service_role`キーはRow Level Securityをバイパスできるため、絶対に公開しないでください。

### 3.3 環境変数設定

`.env`ファイルに以下を追加：

```bash
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...（service_role key）
```

---

## 4. Row Level Security (RLS) 設定

### 4.1 RLSポリシー無効化

このAPIではサーバー側（`service_role`キー）からのみアクセスするため、RLSは不要です。

**確認手順**:

1. 左サイドバーから「Authentication」→「Policies」をクリック
2. `rate_limit_counters`テーブルのRLSが「Disabled」になっていることを確認

**注意**: RLSを有効にする場合は、以下のポリシーを追加：

```sql
-- サービスロールのみアクセス許可
CREATE POLICY "Service role only" ON rate_limit_counters
    FOR ALL
    USING (auth.role() = 'service_role');
```

ただし、`service_role`キーを使用する場合はRLSをバイパスするため、実質的に不要です。

---

## 5. 動作確認

### 5.1 手動テストデータ挿入

SQL Editorで以下を実行：

```sql
-- テストデータ挿入
INSERT INTO rate_limit_counters (uuid, endpoint, count, reset_at)
VALUES (
    '12345678-1234-1234-1234-123456789012',
    '/api/v1/recognize-blood-pressure',
    5,
    NOW() + INTERVAL '1 day'
);

-- データ確認
SELECT * FROM rate_limit_counters;
```

### 5.2 ローカルAPIから接続確認

APIを起動して、ヘルスチェックを実行：

```bash
# APIサーバー起動
uv run uvicorn app.main:app --reload --port 8000

# ヘルスチェック
curl http://localhost:8000/health
```

期待されるレスポンス：

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-22T12:34:56.789Z"
}
```

### 5.3 レート制限動作確認

実際のリクエストでレート制限が動作するか確認：

```bash
# 画像認識API呼び出し（テスト画像必要）
curl -X POST http://localhost:8000/api/v1/recognize-blood-pressure \
  -H "X-User-UUID: 12345678-1234-1234-1234-123456789012" \
  -F "image=@test_image.jpg"
```

Supabaseダッシュボードの「Table Editor」で`rate_limit_counters`テーブルを確認し、カウントが増加していることを確認します。

---

## 6. トラブルシューティング

### 問題1: `relation "rate_limit_counters" does not exist`

**原因**: テーブルが作成されていません。

**解決方法**:
1. SQL Editorで`supabase_schema.sql`のフェーズ1部分を再実行
2. Table Editorでテーブルの存在を確認

### 問題2: `Invalid API key`

**原因**:
- 環境変数が正しく読み込まれていない
- APIキーが間違っている

**解決方法**:
1. `.env`ファイルの`SUPABASE_KEY`が`service_role`キーであることを確認
2. APIサーバーを再起動（`.env`の変更を反映）
3. Supabaseダッシュボードで最新のAPIキーを再取得

### 問題3: `Connection timeout`

**原因**:
- ネットワーク問題
- Supabaseプロジェクトが一時停止中（Freeプランの場合）

**解決方法**:
1. Supabaseダッシュボードでプロジェクトステータスを確認
2. Freeプランの場合、1週間アクティビティがないと一時停止されます
3. プロジェクトを再開してから再試行

### 問題4: `Too many requests`

**原因**: Supabaseの無料プランでは接続数やリクエスト数に制限があります。

**解決方法**:
- **Free Plan制限**:
  - 500MB データベースサイズ
  - 2GB 転送量/月
  - 50,000 月間アクティブユーザー
- 制限を超える場合は、Proプランへアップグレードを検討

### 問題5: `row-level security policy violation`

**原因**: RLSが有効で、ポリシーが設定されていない。

**解決方法**:
```sql
-- RLS無効化
ALTER TABLE rate_limit_counters DISABLE ROW LEVEL SECURITY;
```

または、適切なポリシーを設定（「4. Row Level Security (RLS) 設定」参照）

---

## 次のステップ

Supabaseセットアップが完了したら：

1. **ローカル動作確認**: `SETUP.md`の「6. 動作確認」セクションを実施
2. **フェーズ2準備**: ブラックリスト機能が必要になったら、`supabase_schema.sql`のフェーズ2テーブルを作成
3. **本番環境デプロイ**: Cloud Runへのデプロイ時は、Secret Managerに`SUPABASE_URL`と`SUPABASE_KEY`を保存

---

## 参考リンク

- [Supabase公式ドキュメント](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [PostgreSQL Date/Time Functions](https://www.postgresql.org/docs/current/functions-datetime.html)
