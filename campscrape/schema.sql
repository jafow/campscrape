create table if not exists messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content BYTES NOT NULL,
    created_at TEXT NOT NULL
)
