# Audit Log Queries

Useful queries to analyze your AI-Ready Data assessment history.

## Recent Sessions

```sql
-- Last 10 sessions
SELECT 
    session_id,
    started_at,
    ended_at,
    connection_type,
    scope_summary,
    ROUND((julianday(ended_at) - julianday(started_at)) * 24 * 60, 1) AS duration_minutes
FROM sessions
ORDER BY started_at DESC
LIMIT 10;
```

## Session Details

```sql
-- All events for a specific session
SELECT 
    event_type,
    event_data,
    created_at
FROM events
WHERE session_id = '{session_id}'
ORDER BY created_at;
```

## Assessment History

```sql
-- All assessments with pass/fail summary
SELECT 
    assessment_id,
    connection_sanitized,
    overall_score,
    CASE WHEN l1_pass THEN 'PASS' ELSE 'FAIL' END AS l1,
    CASE WHEN l2_pass THEN 'PASS' ELSE 'FAIL' END AS l2,
    CASE WHEN l3_pass THEN 'PASS' ELSE 'FAIL' END AS l3,
    created_at
FROM assessments
ORDER BY created_at DESC;
```

## Score Trends

```sql
-- Score progression over time
SELECT 
    date(created_at) AS assessment_date,
    connection_sanitized,
    ROUND(AVG(overall_score), 3) AS avg_score,
    SUM(l1_pass) AS l1_passes,
    SUM(l2_pass) AS l2_passes,
    SUM(l3_pass) AS l3_passes,
    COUNT(*) AS assessment_count
FROM assessments
GROUP BY date(created_at), connection_sanitized
ORDER BY assessment_date DESC;
```

## Error Analysis

```sql
-- Recent errors
SELECT 
    s.connection_type,
    json_extract(e.event_data, '$.error') AS error_message,
    json_extract(e.event_data, '$.context') AS context,
    e.created_at
FROM events e
JOIN sessions s ON e.session_id = s.session_id
WHERE e.event_type = 'error'
ORDER BY e.created_at DESC
LIMIT 20;
```

## Command Frequency

```sql
-- Most common commands
SELECT 
    json_extract(event_data, '$.command') AS command,
    COUNT(*) AS times_run
FROM events
WHERE event_type = 'command'
GROUP BY json_extract(event_data, '$.command')
ORDER BY times_run DESC;
```

## Factor Breakdown

```sql
-- Extract factor scores from results JSON (requires results_json structure)
SELECT 
    assessment_id,
    created_at,
    json_extract(results_json, '$.factors.clean.score') AS clean,
    json_extract(results_json, '$.factors.contextual.score') AS contextual,
    json_extract(results_json, '$.factors.consumable.score') AS consumable,
    json_extract(results_json, '$.factors.current.score') AS current,
    json_extract(results_json, '$.factors.correlated.score') AS correlated,
    json_extract(results_json, '$.factors.compliant.score') AS compliant
FROM assessments
ORDER BY created_at DESC;
```

## Activity by Platform

```sql
-- Assessment counts by platform
SELECT 
    s.connection_type AS platform,
    COUNT(DISTINCT s.session_id) AS sessions,
    COUNT(a.assessment_id) AS assessments,
    ROUND(AVG(a.overall_score), 3) AS avg_score
FROM sessions s
LEFT JOIN assessments a ON s.session_id = a.session_id
GROUP BY s.connection_type
ORDER BY assessments DESC;
```

## Data Volume

```sql
-- Database size check
SELECT 
    (SELECT COUNT(*) FROM sessions) AS total_sessions,
    (SELECT COUNT(*) FROM events) AS total_events,
    (SELECT COUNT(*) FROM assessments) AS total_assessments;
```

## Cleanup (Optional)

```sql
-- Delete sessions older than 90 days
DELETE FROM events 
WHERE session_id IN (
    SELECT session_id FROM sessions 
    WHERE started_at < datetime('now', '-90 days')
);

DELETE FROM assessments 
WHERE session_id IN (
    SELECT session_id FROM sessions 
    WHERE started_at < datetime('now', '-90 days')
);

DELETE FROM sessions 
WHERE started_at < datetime('now', '-90 days');

-- Reclaim space
VACUUM;
```
