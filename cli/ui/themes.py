"""AIRD branding colours and Rich theme/style constants.

All colour values are kept here so that every UI surface in the CLI
uses a consistent palette.  Import from ``agent.ui.themes`` rather
than hard-coding colour strings elsewhere.
"""

from rich.theme import Theme

# ---------------------------------------------------------------------------
# Semantic colour tokens
# ---------------------------------------------------------------------------

PASS = "green"
FAIL = "red"
WARN = "yellow"
INFO = "cyan"
MUTED = "dim"

# Factor colours (one per assessment factor)
FACTOR_CLEAN = "bright_green"
FACTOR_CONTEXTUAL = "bright_cyan"
FACTOR_CONSUMABLE = "bright_magenta"
FACTOR_CURRENT = "bright_yellow"
FACTOR_CORRELATED = "bright_blue"
FACTOR_COMPLIANT = "bright_red"

# Structural
HEADER = "bold cyan"
SUBHEADER = "bold"
BORDER = "dim cyan"
ACCENT = "bold magenta"

# ---------------------------------------------------------------------------
# Rich Theme instance (pass to Console for automatic style names)
# ---------------------------------------------------------------------------

AIRD_THEME = Theme(
    {
        "pass": PASS,
        "fail": FAIL,
        "warn": WARN,
        "info": INFO,
        "muted": MUTED,
        "header": HEADER,
        "subheader": SUBHEADER,
        "border": BORDER,
        "accent": ACCENT,
        "factor.clean": FACTOR_CLEAN,
        "factor.contextual": FACTOR_CONTEXTUAL,
        "factor.consumable": FACTOR_CONSUMABLE,
        "factor.current": FACTOR_CURRENT,
        "factor.correlated": FACTOR_CORRELATED,
        "factor.compliant": FACTOR_COMPLIANT,
    }
)

