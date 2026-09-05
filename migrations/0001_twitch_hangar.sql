CREATE TABLE IF NOT EXISTS ax_oauth_states (hash TEXT PRIMARY KEY, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS ax_sessions (hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, login TEXT NOT NULL, token TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS ax_sessions_expiry ON ax_sessions(expires);
CREATE TABLE IF NOT EXISTS ax_app_tokens (id TEXT PRIMARY KEY, token TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS ax_hangar (user_id TEXT NOT NULL, ship_id TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('owned','wishlist','none')), updated INTEGER NOT NULL, PRIMARY KEY(user_id,ship_id));
CREATE TABLE IF NOT EXISTS ax_mutations (user_id TEXT NOT NULL, id TEXT NOT NULL, created INTEGER NOT NULL, PRIMARY KEY(user_id,id));
CREATE TABLE IF NOT EXISTS ax_rate (bucket TEXT NOT NULL, key TEXT NOT NULL, count INTEGER NOT NULL, expires INTEGER NOT NULL, PRIMARY KEY(bucket,key));
