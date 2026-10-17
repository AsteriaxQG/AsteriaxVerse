ALTER TABLE ax_account_users ADD COLUMN email_verified_at INTEGER;

CREATE TABLE IF NOT EXISTS ax_account_email_tokens (
  token_hash TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES ax_account_users(id) ON DELETE CASCADE,
  purpose TEXT NOT NULL CHECK (purpose IN ('verify_email', 'reset_password')),
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ax_account_email_tokens_user_purpose ON ax_account_email_tokens(user_id,purpose);
CREATE INDEX IF NOT EXISTS ax_account_email_tokens_expiry ON ax_account_email_tokens(expires_at);

