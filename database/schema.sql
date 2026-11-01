-- Expense Tracker AI: SQLite schema (Rameen's module, used by Qaim's MCP tools)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,            -- YYYY-MM-DD
    amount REAL NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,          -- YYYY-MM
    category TEXT NOT NULL,       -- category name or 'ALL'
    amount REAL NOT NULL CHECK (amount >= 0),
    UNIQUE (month, category)
);

INSERT OR IGNORE INTO categories (name, description) VALUES
 ('Food', 'Food and dining'),
 ('Transport', 'Transportation'),
 ('Utilities', 'Bills and utilities'),
 ('Entertainment', 'Leisure'),
 ('Shopping', 'Retail purchases'),
 ('Health', 'Healthcare'),
 ('Other', 'Miscellaneous');
