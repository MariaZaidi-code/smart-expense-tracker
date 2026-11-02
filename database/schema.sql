-- Smart Expense Tracker: unified schema.
-- Tables 1-3 are the expense domain (Rameen's normalized model).
-- Tables 4-6 are the agent's short-term + long-term memory and audit trail.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    icon TEXT NOT NULL DEFAULT 'receipt'
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    category_id INTEGER NOT NULL,
    transaction_date TEXT NOT NULL,
    payment_method TEXT NOT NULL DEFAULT 'Card',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    category_id INTEGER,
    amount REAL NOT NULL CHECK (amount > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE (month, category_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_monthly_budget
ON budgets(month) WHERE category_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);

-- ---------------------------------------------------------------------------
-- Agent memory
-- ---------------------------------------------------------------------------

-- Long-term memory: durable user facts/preferences, retrieved in a NEW session.
CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'demo_user',
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'fact',
    importance INTEGER NOT NULL DEFAULT 3,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, memory_key)
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_user ON agent_memory(user_id);

-- Short-term memory: the full transcript of each conversation session.
CREATE TABLE IF NOT EXISTS agent_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'demo_user',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tools_used TEXT NOT NULL DEFAULT '[]',
    sources TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id);

-- Evidence that tools ran, including whether the call used MCP or a local fallback.
CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    arguments TEXT NOT NULL DEFAULT '{}',
    result TEXT NOT NULL DEFAULT '',
    transport TEXT NOT NULL DEFAULT 'local',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_tool_calls_session ON agent_tool_calls(session_id);

-- ---------------------------------------------------------------------------
-- Smart insights (features researched from leading budgeting apps)
-- ---------------------------------------------------------------------------

-- Savings goals / sinking funds (YNAB, Monarch, Qalta).
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    target_amount REAL NOT NULL CHECK (target_amount > 0),
    saved_amount REAL NOT NULL DEFAULT 0 CHECK (saved_amount >= 0),
    target_date TEXT,
    category TEXT NOT NULL DEFAULT 'general',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Merchant -> category rules learned from user corrections (Copilot Money style).
CREATE TABLE IF NOT EXISTS merchant_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    times_used INTEGER NOT NULL DEFAULT 1,
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
