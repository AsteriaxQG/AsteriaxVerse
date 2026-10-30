CREATE TABLE IF NOT EXISTS ax_hangar_insurance (
  user_id TEXT NOT NULL,
  ship_id TEXT NOT NULL,
  term TEXT NOT NULL CHECK(term IN ('6m','24m','120m','lti')),
  updated_at INTEGER NOT NULL,
  PRIMARY KEY(user_id, ship_id)
);
