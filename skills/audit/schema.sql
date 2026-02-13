-- AI-Ready Data Assessment Audit Log Schema
-- Location: ~/.snowflake/cortex/aird-audit.db

-- Sessions track assessment workflows
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    connection_type TEXT,      -- snowflake, duckdb, sqlite, postgres
    scope_summary TEXT         -- e.g., "3 schemas, 47 tables"
);

-- Events log individual actions within a session
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- command, query, assessment, remediation, error
    event_data TEXT,           -- JSON payload with details
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Assessments store full results for later analysis
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    connection_sanitized TEXT, -- connection string with credentials removed
    scope_json TEXT,           -- JSON array of tables assessed
    results_json TEXT,         -- full factor/requirement scores as JSON
    overall_score REAL,        -- 0.0 to 1.0
    l1_pass INTEGER,           -- 1 if passes L1, 0 otherwise
    l2_pass INTEGER,           -- 1 if passes L2, 0 otherwise
    l3_pass INTEGER,           -- 1 if passes L3, 0 otherwise
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_assessments_session ON assessments(session_id);
CREATE INDEX IF NOT EXISTS idx_assessments_created ON assessments(created_at);
