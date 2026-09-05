CREATE TABLE IF NOT EXISTS ax_changelog_publications (
  version TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK(status IN ('sending','published','uncertain')),
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  published_at TEXT,
  discord_message_id TEXT
);
