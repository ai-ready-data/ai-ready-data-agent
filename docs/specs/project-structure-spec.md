# Project Structure Specification

Defines the directory convention for organizing assessment projects — context files, reports, and remediation artifacts.

---

## 1. Purpose

A **project** is a named directory that groups all artifacts for a specific assessment target (a database, a data product, a team's Snowflake account). Projects make assessments organized, repeatable, and shareable.

**Use cases:**
- Assess multiple databases and keep their context/reports separate
- Track a single database over time (re-assess monthly, compare reports)
- Share assessment configuration with a teammate ("here's the project dir")
- Hand off between agent runtimes (context file is runtime-agnostic)

---

## 2. Location

Projects live in the `projects/` directory at the repository root:

```
projects/
├── .gitignore                  # Ignore all projects except sample
├── sample/                     # Committed — example project with sample artifacts
└── <project-name>/             # User-created — .gitignore'd by default
```

Users who want to version their assessments can un-ignore specific project directories.

---

## 3. Directory shape

```
projects/<project-name>/
├── context.yaml                # Discovery answers (M2) — assessment configuration
├── reports/                    # Interpreted assessment reports
│   ├── 2026-02-13T14-30.md
│   └── 2026-02-20T09-15.md
└── remediation/                # Suggested fix scripts
    ├── 2026-02-13T14-30.sql
    └── 2026-02-20T09-15.sql
```

### What lives here vs. elsewhere

| Artifact | Location | Format | Why here / why not |
|----------|----------|--------|--------------------|
| **Context file** | `projects/<name>/context.yaml` | YAML | Per-project config. Reviewed, edited, shared as a document. |
| **Reports** | `projects/<name>/reports/<timestamp>.md` | Markdown | Per-project output. Human-readable, diffable across runs. |
| **Remediation** | `projects/<name>/remediation/<timestamp>.sql` | SQL | Per-project output. User reviews and executes. |
| **Assessment results** | `~/.snowflake/cortex/aird-results.db` | SQLite | Global. Queryable across projects ("compare scores across all my databases"). |
| **Audit log** | `~/.snowflake/cortex/aird-audit.jsonl` | JSONL | Global. Operational trail, not project-specific. |

Assessment results and audit logs are **global** (not per-project) because the primary access patterns are cross-project: "show my last 5 assessments" or "compare scores across databases." The SQLite results database includes `connection_sanitized` and `scope_json` fields that identify which project/database each result came from.

---

## 4. Naming conventions

**Project names:**
- Alphanumeric characters, hyphens, and underscores only
- Lowercase recommended
- Descriptive: include the database or data product name
- Examples: `customer-360-prod`, `analytics-snowflake`, `team-platform-q1`

**Timestamp format for reports and remediation:**
- ISO 8601 with hyphens replacing colons (filesystem-safe): `YYYY-MM-DDTHH-MM`
- Examples: `2026-02-13T14-30.md`, `2026-02-13T14-30.sql`
- UTC recommended

---

## 5. Creating a project

An agent or user creates a project by making the directory structure:

```bash
mkdir -p projects/<project-name>/reports
mkdir -p projects/<project-name>/remediation
```

The `context.yaml` file is created during the discover workflow (Phase 4 of [skills/workflows/discover.md](../../skills/workflows/discover.md)).

Reports and remediation files are created during the interpret and remediate workflow steps.

---

## 6. Sample project

The `projects/sample/` directory is committed to the repo with example artifacts. It demonstrates the project structure and file formats without containing real assessment data.

---

## 7. .gitignore pattern

The `projects/.gitignore` file ignores all project directories except `sample/`:

```
# Ignore all projects (may contain database-specific context)
*
# But keep the directory itself and the sample project
!.gitignore
!sample/
!sample/**
```

Users who want to commit a specific project can add an exception:

```
!my-project/
!my-project/**
```
