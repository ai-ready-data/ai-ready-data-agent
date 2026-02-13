# Snowflake Demo Runbook

**Goal:** Demonstrate AI-Ready Data Assessment across all 6 factors in Snowflake, showing problem detection, AI-assisted remediation, and measurable improvement.

**Duration:** ~15 minutes

**Reference:** `/factors.md` for factor definitions

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Pre-Demo Setup](#2-pre-demo-setup)
3. [Demo Script](#3-demo-script)
4. [Troubleshooting](#4-troubleshooting)

---

## 1. Prerequisites

### 1.1 Snowflake Account

- [ ] Snowflake account with ACCOUNTADMIN or equivalent
- [ ] Warehouse available (COMPUTE_WH or similar)
- [ ] Access to `SNOWFLAKE.ACCOUNT_USAGE` schema

### 1.2 Agent Environment

```bash
# Install agent with Snowflake support
pip install -e ".[snowflake]"

# Verify installation
python -m agent.cli --help
```

### 1.3 Connection String

Set up your connection string:

```bash
# Option 1: Environment variable
export AIRD_CONNECTION_STRING="snowflake://user:pass@account/AIRD_DEMO/ECOMMERCE?warehouse=COMPUTE_WH"

# Option 2: Connection file (more secure)
# Store in ~/.snowflake/connections.toml or use connection name:
# snowflake://connection:my_connection_name
```

---

## 2. Pre-Demo Setup

Run these steps 15-30 minutes before the demo to ensure everything is ready.

### 2.1 Create Demo Database

Run the setup script in Snowflake:

```bash
# Using snowsql
snowsql -a <account> -u <user> -f demo/snowflake_setup.sql

# Or copy/paste into Snowflake worksheet
```

**Expected output:**
- Database: `AIRD_DEMO`
- Schema: `ECOMMERCE`
- Tables: `CUSTOMERS`, `ORDERS`, `ORDER_ITEMS`, `PRODUCTS`, `EVENTS`
- ~70,000 total rows with intentional data quality issues

### 2.2 Create Tags

```bash
snowsql -a <account> -u <user> -f demo/snowflake_tags.sql
```

### 2.3 Verify Agent Connection

```bash
# Test connection
aird discover -c "$AIRD_CONNECTION_STRING"

# Expected: Lists 5 tables in ECOMMERCE schema
```

### 2.4 Pre-Run Assessment (Optional)

Run a quick assessment to verify scores will show expected problems:

```bash
aird assess -c "$AIRD_CONNECTION_STRING" --dry-run
```

---

## 3. Demo Script

### Part 1: The Problem (3 minutes)

**Talking Point:** "You have an e-commerce database. You want to use this data for AI workloads—RAG for customer support, ML for recommendations. Let's see if it's ready."

#### Step 1.1: Run Initial Assessment

```bash
aird assess -c "$AIRD_CONNECTION_STRING" -o markdown
```

**Expected Results:**

| Factor | L1 (Analytics) | L2 (RAG) | L3 (Training) |
|--------|----------------|----------|---------------|
| Clean | ~40% | ~20% | ~10% |
| Contextual | ~25% | ~10% | ~5% |
| Consumable | ~0% | ~0% | ~0% |
| Current | ~20% | ~10% | ~0% |
| Correlated | ~0% | ~0% | ~0% |
| Compliant | ~0% | ~0% | ~0% |

**Talking Points:**
- "This is typical for production data not built with AI in mind"
- "L3 (training) has the strictest requirements—near-zero tolerance for issues"
- "Let's dig into each factor and fix the problems"

---

### Part 2: Factor-by-Factor Fix (10 minutes)

For each factor, explain the problem, run the fix, show the improvement.

#### Factor 0: Clean (~2 min)

**Problem:** High null rates, duplicates, inconsistent formats

```bash
# Show specific Clean failures
aird assess -c "$AIRD_CONNECTION_STRING" --factor clean -o detail
```

**Fix:** Run `demo/reference/snowflake_fix_clean.sql` in Snowflake

**Key fixes applied:**
- Fill null emails/phones
- Deduplicate orders
- Normalize date formats
- Fix type inconsistencies

#### Factor 1: Contextual (~1 min)

**Problem:** No primary keys, no foreign keys, missing temporal columns

**Fix:** Run `demo/reference/snowflake_fix_contextual.sql`

**Key fixes applied:**
- Add PRIMARY KEY to all 5 tables
- Add FOREIGN KEY relationships
- Add updated_at columns

**Talking Point:** "Snowflake PKs and FKs are informational—they don't enforce at DML time, but they document relationships for AI and BI tools."

#### Factor 2: Consumable (~1.5 min)

**Problem:** No documentation, no clustering, no search optimization

**Fix:** Run `demo/reference/snowflake_fix_consumable.sql`

**Key fixes applied:**
- Add table comments
- Add column comments
- Add clustering to large tables
- Enable search optimization

**Talking Point:** "Documentation is critical for AI—LLMs need to understand what data means to use it correctly."

#### Factor 3: Current (~1.5 min)

**Problem:** Stale data, no change tracking, no CDC streams

**Fix:** Run `demo/reference/snowflake_fix_current.sql`

**Key fixes applied:**
- Enable change tracking
- Create streams for CDC
- Add fresh data to EVENTS
- Create dynamic table example

**Talking Point:** "AI models need fresh data. Stale training data = stale predictions."

#### Factor 4: Correlated (~1.5 min)

**Problem:** No tags, no lineage visibility

**Fix:** Run `demo/reference/snowflake_fix_correlated.sql`

**Key fixes applied:**
- Apply data_domain tags
- Apply owner tags
- Apply PII tags to sensitive columns
- Apply freshness SLA tags

**Talking Point:** "Tags enable automated governance and let AI understand data sensitivity."

#### Factor 5: Compliant (~2 min)

**Problem:** PII exposed, no access controls

**Fix:** Run `demo/reference/snowflake_fix_compliant.sql`

**Key fixes applied:**
- Create and apply masking policies
- Create row access policies
- Tag sensitive columns

**Demo the masking:**
```sql
-- As ACCOUNTADMIN (sees full data)
SELECT email, phone, name FROM AIRD_DEMO.ECOMMERCE.CUSTOMERS LIMIT 3;

-- As ANALYST (sees masked data)
USE ROLE ANALYST;
SELECT email, phone, name FROM AIRD_DEMO.ECOMMERCE.CUSTOMERS LIMIT 3;
```

**Talking Point:** "Masking policies protect PII in AI training—the model learns patterns without memorizing personal data."

---

### Part 3: Re-Assessment (2 minutes)

**Talking Point:** "Let's see how much we improved."

```bash
aird assess -c "$AIRD_CONNECTION_STRING" -o markdown --compare
```

**Expected Results (After Fixes):**

| Factor | L1 | L2 | L3 | Improvement |
|--------|----|----|-----|-------------|
| Clean | ~95% | ~90% | ~85% | +50-75% |
| Contextual | ~100% | ~95% | ~90% | +70-85% |
| Consumable | ~90% | ~80% | ~70% | +70-90% |
| Current | ~80% | ~70% | ~60% | +50-70% |
| Correlated | ~90% | ~80% | ~70% | +70-90% |
| Compliant | ~80% | ~70% | ~60% | +60-80% |

**Closing Talking Points:**
- "We went from ~20% average to ~85%+ in under 15 minutes"
- "This data is now ready for RAG workloads (L2)"
- "For training (L3), we'd want to push scores even higher"
- "The agent identified 15+ specific issues; an AI assistant generated SQL fixes"

---

## 4. Troubleshooting

### 4.1 Connection Issues

```bash
# Test basic connectivity
aird discover -c "snowflake://user:pass@account/AIRD_DEMO/ECOMMERCE?warehouse=COMPUTE_WH"

# Check for role/warehouse issues
# Add role explicitly:
# ?warehouse=COMPUTE_WH&role=ACCOUNTADMIN
```

### 4.2 Permission Errors

Some tests require elevated permissions:

| Test | Required Permission |
|------|---------------------|
| Tag queries | GOVERNANCE_VIEWER or ACCOUNTADMIN |
| Access history | GOVERNANCE_VIEWER or ACCOUNTADMIN |
| Network policies | ACCOUNTADMIN |

If running as non-admin, some tests may return 0 (expected).

### 4.3 Tag Latency

`snowflake.account_usage.tag_references` has up to 3-hour latency. If tags were just applied:

- Column/object tag tests may show 0% initially
- Use `SYSTEM$GET_TAG()` for real-time verification
- Wait 3+ hours for full account_usage sync

### 4.4 Empty Results

If Consumable/Current/Correlated/Compliant tests return errors:

1. Verify the YAML files were created correctly
2. Check that requirements are in registry: `aird requirements`
3. Check that suites are discovered: `aird suites`

### 4.5 Reset Demo

To reset and start fresh:

```sql
DROP DATABASE IF EXISTS AIRD_DEMO;
```

Then re-run `snowflake_setup.sql`.

---

## Appendix: Quick Commands

```bash
# Full assessment
aird assess -c "$AIRD_CONNECTION_STRING"

# Single factor
aird assess -c "$AIRD_CONNECTION_STRING" --factor clean

# Specific suite
aird assess -c "$AIRD_CONNECTION_STRING" --suite snowflake_all

# Save results
aird assess -c "$AIRD_CONNECTION_STRING" --save

# Compare to previous run
aird assess -c "$AIRD_CONNECTION_STRING" --compare

# List all suites
aird suites

# List all requirements
aird requirements

# Show history
aird history
```

---

**End of Runbook**
