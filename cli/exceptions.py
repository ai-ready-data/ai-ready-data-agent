"""CLI exception types for exit code mapping. Errors are logged to stderr; machine output stays on stdout."""


class AIRDError(Exception):
    """Base for all CLI errors."""


class UsageError(AIRDError):
    """Invalid arguments or usage. Exit code 2."""


class AssessmentRuntimeError(AIRDError):
    """Connection, execution, or other runtime failure. Exit code 1."""


class DiscoveryError(AIRDError):
    """Failure during schema/table/column discovery."""


class ConfigurationError(AIRDError):
    """Failure loading configuration or context files."""
