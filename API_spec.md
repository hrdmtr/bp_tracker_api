# バックエンドAPI仕様書 v2.0

## 概要
血圧記録アプリ用のバックエンドAPIサービス。画像認識（OpenAI API）と天気情報取得（OpenWeatherMap API）の中継機能を提供。

**重要**: このAPIはデータ保存を一切行わず、外部APIへの代理リクエストのみを提供します。

## ベースURL
```
https://your-api-domain.com/api/v1
```

---

## 基本方針

### データ保存ポリシー
- **サーバー側でデータを一切保存しません**
- 画像認識と天気情報取得の代理（プロキシ）機能のみ
- ユーザーの血圧データ、位置情報、個人情報は保存されません
- すべてのデータはクライアント側（端末）で管理されます

### プライバシー保護
- 位置情報は都市名レベルに粗粒度化してから送信
- 画像データは認識処理後、即座に削除
- アクセスログに個人情報を記録しない
- 第三者へのデータ提供は一切行わない

---

## エンドポイント一覧

### 1. 統合API（推奨）

#### `POST /record-measurement`

血圧計の画像認識と天気情報取得を一度に行う。

**リクエスト**
- Content-Type: `multipart/form-data`
- Parameters:
  - `image` (required): 血圧計の画像ファイル (JPEG/PNG, 最大10MB)
  - `city` (required): 都市名（例: "札幌市", "東京都"）
  - `timestamp` (optional): 測定日時 (ISO 8601形式)

**リクエスト例**:
```bash
curl -X POST https://your-api-domain.com/api/v1/record-measurement \
  -F "image=@blood_pressure_meter.jpg" \
  -F "city=札幌市" \
  -F "timestamp=2025-10-20T10:30:00+09:00"
```

**レスポンス（成功時）**:
```json
{
  "success": true,
  "data": {
    "blood_pressure": {
      "systolic": 128,
      "diastolic": 82,
      "pulse": 72,
      "device_model": "Panasonic EW-BU16"
    },
    "weather": {
      "status": "success",
      "weather": "晴れ",
      "weather_code": "clear",
      "temperature": 23.5,
      "pressure": 1013.2,
      "humidity": 60,
      "city": "札幌市"
    },
    "timestamp": "2025-10-20T10:30:00+09:00"
  }
}
```

**レスポンス（天気取得失敗時）**:
```json
{
  "success": true,
  "data": {
    "blood_pressure": {
      "systolic": 128,
      "diastolic": 82,
      "pulse": 72,
      "device_model": "Panasonic EW-BU16"
    },
    "weather": {
      "status": "failed",
      "error_message": "天気APIが一時的に利用できません"
    },
    "timestamp": "2025-10-20T10:30:00+09:00"
  }
}
```

**エラーレスポンス**:
```json
{
  "success": false,
  "error": {
    "code": "RECOGNITION_FAILED",
    "message": "血圧計の画像を認識できませんでした",
    "reason": "NO_DISPLAY_DETECTED",
    "suggestions": [
      "血圧計の画面全体が写るように撮影してください",
      "明るい場所で撮影してください",
      "画面に反射がないか確認してください"
    ]
  }
}
```

**ステータスコード**:
- `200`: 成功（天気取得失敗でも血圧認識が成功すれば200）
- `400`: リクエストが不正（画像がない、形式が不正など）
- `422`: 画像認識失敗（血圧計が写っていない、読み取り不能など）
- `500`: サーバーエラー

**認識データ詳細**:
- `systolic`: 最高血圧 (mmHg)
- `diastolic`: 最低血圧 (mmHg)
- `pulse`: 脈拍数 (拍/分)
- `device_model`: 血圧計の機種名・型番（認識できない場合は`null`）

**注**: 認識の信頼度（confidence）は、ユーザーが確認画面で目視確認するため、MVPでは実装しません。将来的な自動化機能（フェーズ2以降）で検討予定です。

**天気データ詳細**:
- `status`: 取得ステータス（"success" または "failed"）
- `weather`: 天気の日本語表記（晴れ、曇り、雨、雪など）
- `weather_code`: 天気コード（clear, cloudy, rain, snowなど）
- `temperature`: 気温 (℃)
- `pressure`: 気圧 (hPa)
- `humidity`: 湿度 (%)
- `city`: 都市名（リクエスト時に指定したもの）

---

### 2. 画像認識API（個別）

#### `POST /recognize-blood-pressure`

血圧計の画像から測定値を抽出する。

**リクエスト**
- Content-Type: `multipart/form-data`
- Parameters:
  - `image` (required): 血圧計の画像ファイル (JPEG/PNG)
  - `timestamp` (optional): 測定日時 (ISO 8601形式)

```bash
curl -X POST https://your-api-domain.com/api/v1/recognize-blood-pressure \
  -F "image=@blood_pressure_meter.jpg" \
  -F "timestamp=2025-10-20T10:30:00+09:00"
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "systolic": 128,
    "diastolic": 82,
    "pulse": 72,
    "device_model": "Panasonic EW-BU16",
    "recognized_at": "2025-10-20T10:30:15+09:00"
  }
}
```

**ステータスコード**:
- `200`: 成功
- `400`: リクエストが不正
- `422`: 画像認識失敗
- `500`: サーバーエラー

---

### 3. 天気情報取得API（個別）

#### `GET /weather`

都市名から天気情報（天気、気温、気圧）を取得する。

**リクエスト**
- Parameters:
  - `city` (required): 都市名（例: "札幌市", "東京都"）
  - `timestamp` (optional): 測定日時 (ISO 8601形式)

```bash
curl "https://your-api-domain.com/api/v1/weather?city=札幌市&timestamp=2025-10-20T10:30:00+09:00"
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "weather": "晴れ",
    "weather_code": "clear",
    "temperature": 23.5,
    "pressure": 1013.2,
    "humidity": 60,
    "city": "札幌市",
    "retrieved_at": "2025-10-20T10:30:15+09:00"
  }
}
```

**エラーレスポンス**:
```json
{
  "success": false,
  "error": {
    "code": "WEATHER_API_UNAVAILABLE",
    "message": "天気情報を取得できませんでした",
    "details": "天気APIサービスが一時的に利用できません"
  }
}
```

**ステータスコード**:
- `200`: 成功
- `400`: リクエストが不正（都市名が不正など）
- `503`: 天気APIサービスが利用不可
- `500`: サーバーエラー

**天気コード一覧**:
- `clear`: 晴れ
- `partly_cloudy`: 晴れ時々曇り
- `cloudy`: 曇り
- `rain`: 雨
- `snow`: 雪
- `fog`: 霧
- `thunderstorm`: 雷雨

---

## 認証とセキュリティの段階的実装

このAPIは、セキュリティとユーザー体験のバランスを取りながら、段階的に認証機能を強化していきます。

---

### フェーズ1（MVP - 現在）: ソフトUUID認証

**UUID認証（必須だが事前登録不要）**

すべてのAPIリクエストに以下のヘッダーを含める：
```
X-User-UUID: a3b2c1d4-e5f6-7890-abcd-ef1234567890
```

**特徴**:
- ✅ ユーザー登録不要
- ✅ 任意のUUIDを受け付ける（初回登録なし）
- ✅ すぐに使える（UX優先）
- ✅ レート制限と異常検知で不正利用を防ぐ

**UUIDの生成方法**:
```dart
// アプリ側で生成
import 'package:uuid/uuid.dart';
import 'package:shared_preferences/shared_preferences.dart';

final prefs = await SharedPreferences.getInstance();
String? uuid = prefs.getString('user_uuid');

if (uuid == null) {
  uuid = const Uuid().v4();
  await prefs.setString('user_uuid', uuid);
}
```

**セキュリティ対策**:
1. **厳格なレート制限**
   - UUID単位: 100リクエスト/日
   - IP単位: 1000リクエスト/時間

2. **異常パターン検知**
   - 同じIPから大量の異なるUUID（10以上）
   - 短時間の集中アクセス
   - 異常に高いエラー率（50%以上）

3. **自動一時ブロック**
   - 不正と判断されたUUIDまたはIPを1時間〜24時間ブロック
   - 正常な利用者には影響なし

**エラーレスポンス**:
```json
// UUIDがない場合
{
  "success": false,
  "error": {
    "code": "MISSING_UUID",
    "message": "X-User-UUID ヘッダーが必要です"
  }
}

// 不正利用で一時ブロックされた場合
{
  "success": false,
  "error": {
    "code": "UUID_TEMPORARILY_BLOCKED",
    "message": "異常なアクセスパターンが検出されたため、一時的にブロックされています",
    "reason": "SUSPICIOUS_ACTIVITY",
    "retry_after": 3600,
    "contact": "support@your-domain.com"
  }
}
```

---

### フェーズ2: ブラックリスト導入

**実装タイミング**: 不正利用が増加した場合

**追加機能**:
- 永続的なブラックリストDB
- 繰り返し不正を行うUUIDを恒久的にブロック
- 手動でのブロック/解除機能

**データベース**:
```sql
CREATE TABLE blacklisted_uuids (
  uuid VARCHAR(36) PRIMARY KEY,
  reason TEXT NOT NULL,
  blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  blocked_by VARCHAR(50),
  notes TEXT
);
```

**影響**: 正常なユーザーには影響なし（既存の動作と同じ）

---

### フェーズ3: アプリ登録制（ホワイトリスト）

**実装タイミング**: ユーザー数が大規模になり、厳格な管理が必要な場合

**新規エンドポイント**: アプリ登録API

#### `POST /users/register`

アプリ初回起動時にUUIDを登録する。

**リクエスト**:
```json
{
  "uuid": "a3b2c1d4-e5f6-7890-abcd-ef1234567890",
  "app_version": "1.0.0",
  "platform": "iOS",
  "device_info": {
    "model": "iPhone 14 Pro",
    "os_version": "17.0"
  }
}
```

**レスポンス（成功）**:
```json
{
  "success": true,
  "data": {
    "uuid": "a3b2c1d4-e5f6-7890-abcd-ef1234567890",
    "registered_at": "2025-10-20T10:30:00+09:00",
    "status": "active"
  }
}
```

**レスポンス（既に登録済み）**:
```json
{
  "success": true,
  "data": {
    "uuid": "a3b2c1d4-e5f6-7890-abcd-ef1234567890",
    "registered_at": "2025-10-15T08:20:00+09:00",
    "status": "active",
    "message": "既に登録されています"
  }
}
```

**エラーレスポンス**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_UUID",
    "message": "UUIDの形式が不正です"
  }
}
```

**ステータスコード**:
- `200`: 成功（新規登録または既存）
- `400`: リクエストが不正
- `500`: サーバーエラー

---

#### `GET /users/status`

UUID の登録状態を確認する。

**リクエスト**:
```
GET /users/status
Headers:
  X-User-UUID: a3b2c1d4-e5f6-7890-abcd-ef1234567890
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "uuid": "a3b2c1d4-e5f6-7890-abcd-ef1234567890",
    "status": "active",
    "registered_at": "2025-10-20T10:30:00+09:00",
    "last_access": "2025-10-20T15:45:00+09:00",
    "rate_limit": {
      "daily_limit": 100,
      "used_today": 23,
      "remaining": 77
    }
  }
}
```

**ステータス値**:
- `active`: 正常（アクセス可能）
- `suspended`: 一時停止（不正利用により制限中）
- `blocked`: 永久ブロック
- `unregistered`: 未登録（フェーズ3でのみ発生）

---

#### `POST /users/transfer`

機種変更時に旧UUIDから新UUIDへデータを引き継ぐ。

**リクエスト**:
```json
{
  "old_uuid": "a3b2c1d4-e5f6-7890-abcd-ef1234567890",
  "new_uuid": "b4c3d2e1-f6g7-8901-bcde-fg2345678901",
  "transfer_code": "ABC123"
}
```

**transfer_code の取得方法**:
1. 旧端末で設定画面から「機種変更コード」を表示
2. 6桁のコードが生成される（有効期限: 24時間）
3. 新端末でコードを入力

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "new_uuid": "b4c3d2e1-f6g7-8901-bcde-fg2345678901",
    "transferred_at": "2025-10-20T10:30:00+09:00",
    "old_uuid_status": "retired"
  }
}
```

**エラーレスポンス**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TRANSFER_CODE",
    "message": "転送コードが無効または期限切れです"
  }
}
```

---

#### `POST /users/generate-transfer-code`

機種変更用の転送コードを生成する。

**リクエスト**:
```
POST /users/generate-transfer-code
Headers:
  X-User-UUID: a3b2c1d4-e5f6-7890-abcd-ef1234567890
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "transfer_code": "ABC123",
    "expires_at": "2025-10-21T10:30:00+09:00",
    "valid_for_hours": 24
  }
}
```

---

### フェーズ3での変更点

**既存エンドポイントの変更**:
- `/record-measurement`, `/recognize-blood-pressure`, `/weather` は変更なし
- ただし、**未登録のUUIDはエラーを返す**ようになる

**未登録UUIDのエラーレスポンス**:
```json
{
  "success": false,
  "error": {
    "code": "UUID_NOT_REGISTERED",
    "message": "このUUIDは登録されていません",
    "action": "POST /users/register でUUIDを登録してください"
  }
}
```

**ステータスコード**: `401 Unauthorized`

---

### フェーズ3での移行計画

**既存ユーザーへの対応**:
1. フェーズ3リリースの1ヶ月前に告知
2. 移行期間中（1ヶ月）は未登録UUIDも受け付ける（警告のみ）
3. 移行期間終了後、未登録UUIDは拒否

**アプリ側の実装**:
```dart
// アプリ起動時
final uuid = await UserIdentifier.getUUID();

try {
  // 登録状態を確認
  final status = await api.getUserStatus(uuid);
  
  if (status == 'unregistered') {
    // 未登録なら登録
    await api.registerUser(uuid);
  }
} catch (e) {
  // ネットワークエラー時はスキップ（次回起動時に再試行）
  print('Registration check failed: $e');
}
```

---

### データベース設計（フェーズ3）

```sql
-- 登録ユーザーテーブル
CREATE TABLE registered_users (
  uuid VARCHAR(36) PRIMARY KEY,
  app_version VARCHAR(20),
  platform VARCHAR(20),
  device_model VARCHAR(100),
  os_version VARCHAR(50),
  registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_access TIMESTAMP,
  status VARCHAR(20) DEFAULT 'active',
  INDEX idx_status (status),
  INDEX idx_last_access (last_access)
);

-- 転送コードテーブル
CREATE TABLE transfer_codes (
  code VARCHAR(6) PRIMARY KEY,
  uuid VARCHAR(36) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  used BOOLEAN DEFAULT FALSE,
  used_at TIMESTAMP,
  new_uuid VARCHAR(36),
  INDEX idx_uuid (uuid),
  INDEX idx_expires (expires_at)
);

-- ブラックリストテーブル
CREATE TABLE blacklisted_uuids (
  uuid VARCHAR(36) PRIMARY KEY,
  reason TEXT NOT NULL,
  blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  blocked_by VARCHAR(50),
  notes TEXT
);
```

---

### 段階的リリースのまとめ

| フェーズ | 実装内容 | UUID登録 | 主な目的 |
|---------|---------|---------|---------|
| **フェーズ1（現在）** | ソフトUUID認証<br>レート制限<br>異常検知 | 不要 | UX優先<br>シンプル |
| **フェーズ2** | ブラックリスト追加 | 不要 | 不正利用対策強化 |
| **フェーズ3** | アプリ登録制<br>ホワイトリスト<br>機種変更対応 | 必須 | 厳格な管理<br>大規模運用 |

**移行の判断基準**:
- フェーズ1→2: 不正利用の増加が見られた場合
- フェーズ2→3: ユーザー数が1万人を超えた場合、またはコスト管理が必要な場合

---

## エラーコード一覧

| コード | 説明 |
|--------|------|
| `INVALID_REQUEST` | リクエストが不正 |
| `MISSING_PARAMETER` | 必須パラメータが不足 |
| `MISSING_UUID` | X-User-UUID ヘッダーが不足 |
| `INVALID_UUID` | UUIDの形式が不正 |
| `UUID_NOT_REGISTERED` | UUID未登録（フェーズ3のみ） |
| `UUID_TEMPORARILY_BLOCKED` | 異常アクセスにより一時ブロック |
| `UUID_BLOCKED` | UUIDが永久ブロックされている |
| `INVALID_IMAGE` | 画像形式が不正またはファイルが壊れている |
| `IMAGE_TOO_LARGE` | 画像サイズが大きすぎる（上限: 10MB） |
| `RECOGNITION_FAILED` | 画像認識失敗 |
| `NO_DISPLAY_DETECTED` | 血圧計の画面が検出できない |
| `BLUR_IMAGE` | 画像がぼやけている |
| `WEATHER_API_UNAVAILABLE` | 天気API利用不可 |
| `INVALID_CITY` | 都市名が不正または見つからない |
| `RATE_LIMIT_EXCEEDED` | レート制限超過 |
| `INVALID_TRANSFER_CODE` | 機種変更コードが無効（フェーズ3） |
| `INTERNAL_SERVER_ERROR` | サーバー内部エラー |

---

## レート制限

### フェーズ1（現在）: 二段階レート制限

#### UUID単位の制限（主要）

**画像認識API** (`/recognize-blood-pressure`):
- 100リクエスト/日/UUID

**天気情報API** (`/weather`):
- 500リクエスト/日/UUID

**統合API** (`/record-measurement`):
- 100リクエスト/日/UUID

#### IPアドレス単位の制限（補助）

悪意のある攻撃を防ぐため、IPアドレス単位でも制限：
- 1000リクエスト/時間/IPアドレス

#### レスポンスヘッダー

各レスポンスに残り回数を含める：
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1634745600
X-RateLimit-Reset-Human: 2025-10-21T00:00:00+09:00
```

#### レート制限超過時

ステータスコード: `429 Too Many Requests`

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "1日のリクエスト上限（100回）に達しました",
    "retry_after": 43200,
    "limit": 100,
    "remaining": 0,
    "reset_at": "2025-10-21T00:00:00+09:00"
  }
}
```

### フェーズ2以降: 同様の制限を継続

レート制限の基本方針は変更なし。ただし、ブラックリストやホワイトリストと組み合わせて運用。

---

## セキュリティ

### HTTPS必須
すべてのAPIエンドポイントはHTTPS（TLS 1.2以上）経由でのみアクセス可能。

### データ保持ポリシー

**処理中のデータ**:
- 画像データ: メモリ上で処理、認識後即座に削除
- 位置情報（都市名）: リクエスト処理中のみメモリに保持
- 認識結果: レスポンス送信後、破棄

**ログ**:
- アクセスログ: IPアドレス、エンドポイント、ステータスコードのみ
- 個人情報（血圧値、機種名、都市名など）はログに記録しない
- ログ保持期間: 30日（トラブルシューティング用）

**バックアップ**:
- データベース: 存在しない（データを保存しないため）
- ユーザーデータ: 保存しないため、バックアップ対象外

### APIキーの管理（サーバー側）

```bash
# 環境変数で管理
OPENAI_API_KEY=sk-xxxxx
OPENWEATHERMAP_API_KEY=xxxxx

# 本番環境ではシークレット管理サービスを使用
# - AWS Secrets Manager
# - Google Cloud Secret Manager
# - Azure Key Vault
```

---

## 実装ノート

### OpenAI APIとの連携

**使用モデル**:
- `gpt-4o` または `gpt-4o-mini`
- Vision機能を使用

**プロンプト例**:
```
あなたは血圧計の画像を解析する専門システムです。
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
}
```

**注**: 認識の信頼度（confidence）は、ユーザーが確認画面で目視確認を行うため、プロンプトには含めていません。将来的に自動化を進める場合（フェーズ2以降）に追加を検討します。

**エラーハンドリング**:
- OpenAI APIタイムアウト: 30秒
- エラー時は `RECOGNITION_FAILED` を返す
- リトライ: 実装しない（ユーザーに再撮影を促す）

---

### OpenWeatherMap APIとの連携

**使用API**:
- Current Weather Data API
- エンドポイント: `https://api.openweathermap.org/data/2.5/weather`

**リクエストパラメータ**:
```
q={city},JP
units=metric
lang=ja
appid={API_KEY}
```

**都市名の変換**:
- クライアントから受け取った日本語都市名を英語に変換
- 例: "札幌市" → "Sapporo"
- 変換テーブルを内部で保持

**天気コードの日本語変換**:
OpenWeatherMapの天気コードを日本語に変換するテーブルを用意:
```javascript
const weatherTranslation = {
  'Clear': '晴れ',
  'Clouds': '曇り',
  'Rain': '雨',
  'Snow': '雪',
  'Fog': '霧',
  'Thunderstorm': '雷雨',
  // ...
};
```

**エラーハンドリング**:
- OpenWeatherMap APIタイムアウト: 10秒
- エラー時は統合APIでも成功レスポンス（weather.status: "failed"）
- 無効な都市名: 400エラー

---

## データフロー図

```
[アプリ（クライアント）]
  ↓ 1. 画像 + 都市名 + タイムスタンプ
[バックエンドAPI]
  ↓ 2-1. 画像認識リクエスト
[OpenAI API]
  ↓ 2-2. 認識結果（血圧値、機種名）
[バックエンドAPI]
  ↓ 3-1. 天気情報リクエスト
[OpenWeatherMap API]
  ↓ 3-2. 天気データ
[バックエンドAPI]
  ↓ 4. 統合結果を返却（保存はしない）
[アプリ（クライアント）]
  ↓ 5. ローカルDBに保存
[端末内SQLite]
```

**重要**: バックエンドAPIは中継のみ行い、データを保存しません。

---

## プライバシーとコンプライアンス

### 個人情報保護

**取り扱う情報**:
- 血圧測定値（要配慮個人情報）
- 位置情報（都市名レベルに粗粒度化）
- 血圧計機種情報

**保存しない方針**:
- サーバー側でこれらの情報を一切保存しない
- 処理中のみメモリに保持
- 第三者への提供なし

**法的根拠**:
- 個人情報保護法: データを保有しないため、管理義務なし
- GDPR: 将来的に海外展開する場合も、データ保存なしでコンプライアンス負担軽減

### ユーザーへの透明性

アプリ内で以下を明示:
```
【データの取り扱い】
- あなたの血圧データは、あなたの端末内にのみ保存されます
- サーバーには一時的に送信されますが、保存されません
- 開発者はあなたのデータにアクセスできません
- データの所有者は完全にあなたです
```

---

## バージョン履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|----------|
| 1.0 | 2025-10-20 | 初版作成 |
| 2.0 | 2025-10-20 | 統合API追加、認証方針更新、プライバシー方針明確化、位置情報を都市名に変更 |

---

## 将来の拡張（検討中）

### フェーズ2以降で検討する機能

**セキュリティ・認証関連**:
1. ✅ **ブラックリスト機能**（フェーズ2）
2. ✅ **UUID登録制**（フェーズ3）
3. ✅ **機種変更対応**（フェーズ3）
4. **APIキー認証**（エンタープライズ向け）

**機能拡張**:
1. **過去データ対応**: 5日以内の測定なら過去の天気を取得
2. **バッチ処理**: 複数画像の一括認識
3. **Webhook**: 認識完了時の通知
4. **統計API**: 匿名化された全体統計（個人は特定不可）
5. **認識信頼度（confidence）**: LLMに画像の鮮明度を評価させ、自動化に活用

**実装優先度**:
ユーザーフィードバックとニーズに応じて決定します。

---

## 移行ガイド（各フェーズ）

### フェーズ1→フェーズ2への移行

**アプリ側の変更**: なし  
**サーバー側の変更**: ブラックリストDB追加のみ  
**ユーザーへの影響**: なし（通常利用では気づかない）

### フェーズ2→フェーズ3への移行

**告知期間**: 1ヶ月前に告知

**移行期間（1ヶ月）**:
- 未登録UUIDも受け付ける
- レスポンスに警告を含める：
```json
{
  "success": true,
  "data": { ... },
  "warning": {
    "code": "UUID_REGISTRATION_REQUIRED_SOON",
    "message": "2025年12月1日以降、UUID登録が必須になります",
    "action": "POST /users/register で登録してください"
  }
}
```

**移行期間終了後**:
- 未登録UUIDは `401 Unauthorized` を返す
- アプリは起動時に自動登録を試みる

**アプリ側の実装例**:
```dart
// アプリ起動時のチェック
Future<void> ensureUUIDRegistered() async {
  final uuid = await UserIdentifier.getUUID();
  
  try {
    final status = await api.getUserStatus(uuid);
    
    if (status == 'unregistered') {
      await api.registerUser(uuid);
      print('UUID registered successfully');
    }
  } catch (e) {
    // ネットワークエラー時は次回リトライ
    print('UUID registration check failed: $e');
  }
}
```

---

## サポート・問い合わせ

**技術サポート**: tech-support@your-domain.com  
**プライバシーに関する問い合わせ**: privacy@your-domain.com  

**ドキュメント更新**: このAPI仕様書は随時更新されます。最新版は常にこのURLで確認できます。