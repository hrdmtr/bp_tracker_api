# 開発ガイド

このプロジェクトへの貢献方法を説明します。

## ブランチ戦略

### ブランチ構成

```
main (本番環境)
  ↑
develop (開発環境)
  ↑
feature/xxx (機能開発)
```

### ブランチの役割

- **main**: 本番環境にデプロイされる安定版
- **develop**: 開発中の最新コード、次のリリース候補
- **feature/xxx**: 個別の機能開発・バグ修正

## 開発フロー

### 1. 新機能・バグ修正を開始

developブランチから新しいfeatureブランチを作成：

```bash
git checkout develop
git pull origin develop
git checkout -b feature/機能名
```

**ブランチ名の規則**:
- `feature/機能名`: 新機能開発
- `feature/fix-バグ名`: バグ修正
- `feature/refactor-対象`: リファクタリング
- `feature/docs-対象`: ドキュメント更新

例:
```bash
git checkout -b feature/add-email-notification
git checkout -b feature/fix-rate-limit-bug
git checkout -b feature/refactor-openai-service
```

### 2. 実装

```bash
# コード変更
# テスト追加
uv run pytest

# コミット
git add .
git commit -m "feat: 機能の説明"
```

**コミットメッセージの規則**:
- `feat:` 新機能
- `fix:` バグ修正
- `refactor:` リファクタリング
- `docs:` ドキュメント更新
- `test:` テスト追加・更新
- `chore:` ビルド・設定変更

### 3. プッシュしてプルリクエスト作成

```bash
git push -u origin feature/機能名
```

GitHubでプルリクエストを作成：
- **Base**: `develop`
- **Compare**: `feature/機能名`

### 4. レビュー・マージ

- コードレビューを受ける
- 必要に応じて修正
- レビュー承認後、developにマージ

### 5. リリース

developが安定したら、mainにマージしてデプロイ：

```bash
git checkout main
git merge develop
git push origin main
```

## 開発環境セットアップ

```bash
# 依存関係インストール
uv sync

# 環境変数設定
cp .env.example .env
# .envを編集

# Supabaseテーブル作成
# supabase_schema.sqlを実行

# 開発サーバー起動
uv run uvicorn app.main:app --reload
```

## テスト

### 全テスト実行

```bash
uv run pytest
```

### カバレッジ付きテスト

```bash
uv run pytest --cov=app --cov-report=html
```

### 特定のテストのみ

```bash
uv run pytest tests/test_api/test_measurement.py
```

## コードスタイル

### Ruffによるフォーマット・Lint

```bash
# フォーマット
uv run ruff format app tests

# Lint
uv run ruff check app tests

# 自動修正
uv run ruff check --fix app tests
```

## API仕様の更新

APIに変更を加えた場合は、以下を更新：

1. **API_spec.md**: API仕様書
2. **OpenAPIドキュメント**: FastAPIの自動生成（`/docs`）
3. **CLAUDE.md**: 必要に応じて更新

## プルリクエストのガイドライン

### 必須事項

- [ ] テストが追加されている
- [ ] すべてのテストが成功している
- [ ] ドキュメントが更新されている（必要な場合）
- [ ] コミットメッセージが規則に従っている
- [ ] 破壊的変更がある場合は明記

### PRの説明に含めること

- 変更の概要
- 変更理由
- テスト方法
- スクリーンショット（UIに変更がある場合）

## 質問・サポート

- **技術的な質問**: GitHub Issueを作成
- **バグ報告**: GitHub Issueを作成（バグ報告テンプレート使用）
- **機能提案**: GitHub Issueを作成（機能提案テンプレート使用）

## ライセンス

(TBD)
