"""Interactive discovery-scope selection: tree view and table picker.

After ``discover()`` returns an inventory dict, these helpers let the
user visually inspect the schema/table hierarchy and choose which
tables to include in the assessment run.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from rich.tree import Tree

from agent.ui.console import get_console


# ---------------------------------------------------------------------------
# Tree view
# ---------------------------------------------------------------------------


def show_discovery_tree(inventory: dict) -> None:
    """Render a Rich Tree showing schemas → tables with column counts.

    Parameters
    ----------
    inventory:
        The dict returned by ``discover()`` with keys
        ``schemas``, ``tables``, and ``columns``.
    """
    console = get_console()

    # Build column-count lookup: (schema, table) -> count
    col_counts: Dict[str, int] = defaultdict(int)
    for col in inventory.get("columns", []):
        key = "{}.{}".format(col["schema"], col["table"])
        col_counts[key] += 1

    # Group tables by schema
    schema_tables: Dict[str, List[dict]] = defaultdict(list)
    for tbl in inventory.get("tables", []):
        schema_tables[tbl["schema"]].append(tbl)

    tree = Tree("[header]Discovered Schema[/header]", guide_style="border")

    for schema in sorted(schema_tables.keys()):
        tables = schema_tables[schema]
        branch = tree.add(
            "[accent]{schema}[/accent]  [muted]({n} table{s})[/muted]".format(
                schema=schema,
                n=len(tables),
                s="" if len(tables) == 1 else "s",
            )
        )
        for tbl in sorted(tables, key=lambda t: t["table"]):
            ncols = col_counts.get(tbl["full_name"], 0)
            branch.add(
                "{table}  [muted]({n} col{s})[/muted]".format(
                    table=tbl["table"],
                    n=ncols,
                    s="" if ncols == 1 else "s",
                )
            )

    console.print()
    console.print(tree)
    console.print()


# ---------------------------------------------------------------------------
# Multi-select table picker
# ---------------------------------------------------------------------------

SELECT_ALL_LABEL = "» Select All"


def select_tables(inventory: dict) -> List[str]:
    """Prompt the user to choose tables via ``questionary.checkbox``.

    Choices are grouped by schema.  A *Select All* option is provided
    as the first entry.  Returns a list of ``full_name`` strings
    (e.g. ``["main.customers", "main.orders"]``).

    If the user selects *Select All*, every table is returned.
    If the user cancels (Ctrl-C / empty), returns all tables (no filter).
    """
    import questionary

    # Build grouped choices
    schema_tables: Dict[str, List[dict]] = defaultdict(list)
    for tbl in inventory.get("tables", []):
        schema_tables[tbl["schema"]].append(tbl)

    all_names: List[str] = []
    choices: list = [
        questionary.Choice(title=SELECT_ALL_LABEL, value=SELECT_ALL_LABEL, checked=False),
        questionary.Separator("─" * 40),
    ]

    for schema in sorted(schema_tables.keys()):
        choices.append(questionary.Separator("  {} ".format(schema)))
        for tbl in sorted(schema_tables[schema], key=lambda t: t["table"]):
            full = tbl["full_name"]
            all_names.append(full)
            choices.append(
                questionary.Choice(
                    title="  {table}".format(table=tbl["table"]),
                    value=full,
                    checked=True,
                )
            )

    result = questionary.checkbox(
        "Select tables to include in assessment:",
        choices=choices,
    ).ask()

    # Ctrl-C or empty → return all (no filtering)
    if not result:
        return all_names

    if SELECT_ALL_LABEL in result:
        return all_names

    return [r for r in result if r != SELECT_ALL_LABEL]


# ---------------------------------------------------------------------------
# Inventory filter
# ---------------------------------------------------------------------------


def filter_inventory(inventory: dict, selected_tables: List[str]) -> dict:
    """Return a new inventory containing only *selected_tables*.

    Parameters
    ----------
    inventory:
        Original inventory dict from ``discover()``.
    selected_tables:
        List of ``full_name`` strings to keep.

    Returns a new dict with the same structure (schemas, tables, columns)
    but limited to the selected tables.
    """
    keep = set(selected_tables)

    tables = [t for t in inventory.get("tables", []) if t["full_name"] in keep]
    # Derive schemas from kept tables
    schemas = sorted({t["schema"] for t in tables})
    # Keep only columns belonging to kept tables
    table_keys = {(t["schema"], t["table"]) for t in tables}
    columns = [
        c for c in inventory.get("columns", [])
        if (c["schema"], c["table"]) in table_keys
    ]

    return {
        "schemas": schemas,
        "tables": tables,
        "columns": columns,
    }

