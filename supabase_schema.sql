-- Supabaseテーブル定義
-- フェーズ1: レート制限カウンターテーブル

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

-- ===================================================================
-- フェーズ2以降: ブラックリストテーブル（初期は不要）
-- ===================================================================

-- ブラックリストテーブル（フェーズ2で作成）
CREATE TABLE IF NOT EXISTS blacklisted_uuids (
    uuid VARCHAR(36) PRIMARY KEY,
    reason TEXT NOT NULL,
    blocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    blocked_by VARCHAR(50),
    notes TEXT
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_blacklisted_uuid ON blacklisted_uuids(uuid);

-- コメント追加
COMMENT ON TABLE blacklisted_uuids IS 'ブラックリスト（不正利用UUID）';
COMMENT ON COLUMN blacklisted_uuids.uuid IS 'ブロック対象UUID';
COMMENT ON COLUMN blacklisted_uuids.reason IS 'ブロック理由';
COMMENT ON COLUMN blacklisted_uuids.blocked_at IS 'ブロック日時';
COMMENT ON COLUMN blacklisted_uuids.blocked_by IS 'ブロック実施者';

-- ===================================================================
-- フェーズ3以降: UUID登録テーブル・転送コードテーブル（初期は不要）
-- ===================================================================

-- 登録ユーザーテーブル（フェーズ3で作成）
CREATE TABLE IF NOT EXISTS registered_users (
    uuid VARCHAR(36) PRIMARY KEY,
    app_version VARCHAR(20),
    platform VARCHAR(20),
    device_model VARCHAR(100),
    os_version VARCHAR(50),
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_access TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active'
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_registered_users_status ON registered_users(status);
CREATE INDEX IF NOT EXISTS idx_registered_users_last_access ON registered_users(last_access);

-- コメント追加
COMMENT ON TABLE registered_users IS '登録ユーザー（フェーズ3）';
COMMENT ON COLUMN registered_users.status IS 'ステータス（active/suspended/blocked）';

-- 転送コードテーブル（フェーズ3で作成）
CREATE TABLE IF NOT EXISTS transfer_codes (
    code VARCHAR(6) PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE,
    new_uuid VARCHAR(36)
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_transfer_codes_uuid ON transfer_codes(uuid);
CREATE INDEX IF NOT EXISTS idx_transfer_codes_expires ON transfer_codes(expires_at);

-- コメント追加
COMMENT ON TABLE transfer_codes IS '機種変更用転送コード（フェーズ3）';
COMMENT ON COLUMN transfer_codes.code IS '6桁の転送コード';
COMMENT ON COLUMN transfer_codes.uuid IS '旧UUID';
COMMENT ON COLUMN transfer_codes.new_uuid IS '新UUID（使用後）';
