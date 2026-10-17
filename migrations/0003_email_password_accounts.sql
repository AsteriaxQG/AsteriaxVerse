ALTER TABLE ax_account_users ADD COLUMN display_name TEXT NOT NULL DEFAULT '';
ALTER TABLE ax_account_users ADD COLUMN password_salt TEXT NOT NULL DEFAULT '';
ALTER TABLE ax_account_users ADD COLUMN password_hash TEXT NOT NULL DEFAULT '';

DROP TABLE IF EXISTS ax_account_login_codes;


