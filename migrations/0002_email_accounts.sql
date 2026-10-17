CREATE TABLE IF NOT EXISTS ax_account_users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL COLLATE NOCASE UNIQUE,
  created_at INTEGER NOT NULL,
  last_login_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ax_account_login_codes (
  email TEXT PRIMARY KEY COLLATE NOCASE,
  code_hash TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ax_account_sessions (
  token_hash TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES ax_account_users(id) ON DELETE CASCADE,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ax_account_sessions_expiry ON ax_account_sessions(expires_at);

CREATE TABLE IF NOT EXISTS ax_account_hangars (
  user_id TEXT PRIMARY KEY REFERENCES ax_account_users(id) ON DELETE CASCADE,
  owned_json TEXT NOT NULL DEFAULT '[]',
  wishlist_json TEXT NOT NULL DEFAULT '[]',
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ax_account_rate_limits (
  bucket TEXT NOT NULL,
  window_start INTEGER NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(bucket,window_start)
);
CREATE INDEX IF NOT EXISTS ax_account_rate_limits_expiry ON ax_account_rate_limits(window_start);

