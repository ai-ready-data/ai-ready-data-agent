"""Remediation templates per requirement key. Used by fix command to generate actionable suggestions."""

# Each template: (description, sql_or_guidance)
# Placeholders: {schema}, {table}, {column} — column may be empty for table-level tests
REMEDIATION_TEMPLATES = {
    "null_rate": (
        "High null rate in column. Consider backfilling or setting a default.",
        """-- Option 1: Backfill existing nulls with a default
UPDATE {schema}.{table} SET {column} = 'Unknown' WHERE {column} IS NULL;

-- Option 2: Add default for future inserts (adjust default_value for your domain)
-- ALTER TABLE {schema}.{table} ALTER COLUMN {column} SET DEFAULT 'default_value';""",
    ),
    "duplicate_rate": (
        "Duplicate rows detected. Consider deduplication or adding a unique constraint.",
        """-- Investigate duplicates first (list all columns in GROUP BY)
-- SELECT col1, col2, COUNT(*) FROM {schema}.{table} GROUP BY col1, col2 HAVING COUNT(*) > 1;

-- Option: Add unique constraint to prevent future duplicates
-- ALTER TABLE {schema}.{table} ADD CONSTRAINT uq_{table} UNIQUE (column_list);""",
    ),
    "primary_key_defined": (
        "Table has no primary key. Add a PK for reliable joins and traceability.",
        """-- Option 1: Add primary key on existing column (e.g. id)
ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_{table} PRIMARY KEY (id);

-- Option 2: Add surrogate key if no natural key exists
ALTER TABLE {schema}.{table} ADD COLUMN id SERIAL PRIMARY KEY;

-- dbt: generate surrogate key macro
-- {{ generate_surrogate_key(['col1', 'col2']) }}""",
    ),
    "foreign_key_coverage": (
        "Table has no foreign key constraints. Add FKs to declare relationships.",
        """-- Add foreign key (adjust referenced table/column)
ALTER TABLE {schema}.{table}
ADD CONSTRAINT fk_{table}_ref
FOREIGN KEY (ref_column) REFERENCES other_schema.other_table(id);""",
    ),
    "temporal_scope_present": (
        "Table lacks temporal columns (created_at, updated_at). Add for freshness tracking.",
        """-- Add temporal columns
ALTER TABLE {schema}.{table} ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE {schema}.{table} ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;""",
    ),
    "semantic_model_coverage": (
        "Table not represented in semantic model. Add to semantic layer or create view.",
        """-- Create a view or add to your semantic model (dbt, LookML, etc.)
-- Example: dbt model
-- {{ config(materialized='view') }}
-- SELECT * FROM {schema}.{table}""",
    ),
    "constraint_coverage": (
        "Table has no constraints. Add primary key or unique constraint.",
        """-- Add primary key or unique constraint
ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_{table} PRIMARY KEY (id);""",
    ),
    "column_comment_coverage": (
        "Column lacks documentation. Add column comments.",
        """-- Add column comment (syntax varies by platform)
COMMENT ON COLUMN {schema}.{table}.{column} IS 'Description of this column';""",
    ),
    "table_comment_coverage": (
        "Table lacks documentation. Add table comment.",
        """-- Add table comment (syntax varies by platform)
COMMENT ON TABLE {schema}.{table} IS 'Description: grain and primary key';""",
    ),
}
