-- Comptes du Hangar. La route Pages initialise aussi ces tables si la migration
-- n'a pas encore été exécutée sur AX_DB.
CREATE TABLE IF NOT EXISTS ax_hangar_users (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE, display_name TEXT NOT NULL, password_salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS ax_hangar_sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS ax_hangar_items (user_id TEXT NOT NULL, ship_id TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('owned','wishlist')), updated_at INTEGER NOT NULL, PRIMARY KEY(user_id,ship_id));
CREATE TABLE IF NOT EXISTS ax_hangar_attempts (bucket TEXT PRIMARY KEY, hits INTEGER NOT NULL, reset_at INTEGER NOT NULL);
