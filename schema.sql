-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Table for saving all generated quotes
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_text TEXT NOT NULL,
    author TEXT NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Unique index to prevent duplicate quote texts from the same author
CREATE UNIQUE INDEX IF NOT EXISTS idx_quotes_text_author ON quotes (quote_text, author);

-- Table for user favorited quotes
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id INTEGER NOT NULL UNIQUE,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
);

-- Table for user-defined collections
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Mapping table between collections and quotes
CREATE TABLE IF NOT EXISTS collection_quotes (
    collection_id INTEGER NOT NULL,
    quote_id INTEGER NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, quote_id),
    FOREIGN KEY(collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
);

-- Table for tracking the Daily Quote
CREATE TABLE IF NOT EXISTS daily_quotes (
    date TEXT PRIMARY KEY, -- format YYYY-MM-DD
    quote_id INTEGER NOT NULL,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(quote_id) REFERENCES quotes(id) ON DELETE CASCADE
);

-- Table for logging dashboard activities
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_type TEXT NOT NULL, -- 'generate', 'favorite', 'unfavorite', 'collection_create', 'collection_add', 'collection_remove'
    description TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
