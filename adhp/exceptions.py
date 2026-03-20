"""ADHP SDK exceptions."""


class ADHPError(Exception):
    """Base exception for all ADHP errors."""


class ADHPConfigError(ADHPError):
    """Raised when an ADHP configuration is invalid or cannot be loaded."""


class ADHPComplianceError(ADHPError):
    """Raised when a compliance check fails."""

    def __init__(self, message: str, checks: list | None = None):
        super().__init__(message)
        self.checks = checks or []


class ADHPConnectionError(ADHPError):
    """Raised when connection to an MCP server fails."""


class ADHPValidationError(ADHPError):
    """Raised when JSON Schema validation fails."""

    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []
