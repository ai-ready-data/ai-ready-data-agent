---
name: audit
description: "Audit logging for AI-Ready Data assessments. Enabled by default. Tracks sessions, commands, queries, and results to local SQLite."
---

# Audit Logging

All AI-Ready Data assessment activity is logged by default to a local SQLite database for history, debugging, and compliance.

**This is enabled by default.** To disable, the user must explicitly pass `--no-audit`.

## Database Location

```
~/.snowflake/cortex/aird-audit.db
```

## Setup

Before starting an assessment session with audit logging, initialize the database:

```bash
# Create database and schema (idempotent)
sqlite3 ~/.snowflake/cortex/aird-audit.db < /path/to/skills/audit/schema.sql
```

Or execute the schema SQL directly:

```sql
-- Run against ~/.snowflake/cortex/aird-audit.db
-- See schema.sql for full DDL
```

## Workflow

### 1. Start Session

At the beginning of an assessment workflow, create a session record:

```sql
INSERT INTO sessions (session_id, started_at, connection_type)
VALUES (
    lower(hex(randomblob(16))),  -- generates UUID-like ID
    datetime('now'),
    '{platform}'                  -- snowflake, duckdb, sqlite
);
```

Store the `session_id` for use in subsequent logging.

### 2. Log Events

Log each significant action during the session:

**Command executed:**
```sql
INSERT INTO events (session_id, event_type, event_data)
VALUES (
    '{session_id}',
    'command',
    json_object('command', 'aird assess', 'args', '-c duckdb://file.db -o markdown')
);
```

**Query executed:**
```sql
INSERT INTO events (session_id, event_type, event_data)
VALUES (
    '{session_id}',
    'query',
    json_object('sql', 'SELECT COUNT(*) FROM information_schema.tables', 'rows_returned', 47)
);
```

**Error occurred:**
```sql
INSERT INTO events (session_id, event_type, event_data)
VALUES (
    '{session_id}',
    'error',
    json_object('error', 'Connection refused', 'context', 'discovery phase')
);
```

### 3. Log Assessment Results

After an assessment completes, log the full results:

```sql
INSERT INTO assessments (
    assessment_id,
    session_id,
    connection_sanitized,
    scope_json,
    results_json,
    overall_score,
    l1_pass,
    l2_pass,
    l3_pass
)
VALUES (
    '{assessment_id}',
    '{session_id}',
    'duckdb://****',              -- credentials removed
    '["main.users", "main.orders"]',
    '{full_results_json}',
    0.78,
    1,  -- passes L1
    1,  -- passes L2
    0   -- fails L3
);
```

### 4. End Session

When the assessment workflow completes:

```sql
UPDATE sessions
SET ended_at = datetime('now'),
    scope_summary = '2 schemas, 15 tables'
WHERE session_id = '{session_id}';
```

## Sanitization Rules

**Never log:**
- Passwords or tokens
- Full connection strings with credentials
- Sensitive data values from queries

**Always sanitize:**
- Replace passwords with `****`
- Replace tokens with `[REDACTED]`
- Log query structure, not result data

## Integration with Assessment Workflow

When audit logging is enabled:

1. **Before discovery**: Start session, log connection type
2. **During discovery**: Log discovery queries
3. **During assessment**: Log each test query
4. **After scoring**: Log full assessment results
5. **After remediation suggestions**: Log suggested fixes (not user data)
6. **On completion**: End session with scope summary

## Querying Audit History

See [queries.md](queries.md) for useful queries to analyze your audit log.

## Constraints

- **Read-only to user data**: Audit logging only writes to the local audit database
- **No credentials**: Never log passwords, tokens, or secrets
- **Local only**: This skill logs to local SQLite; Snowflake logging is a future extension
