"""ADHP SDK — Agent Data Handling Policy compliance for MCP servers and clients.

Quick start::

    from adhp import ADHPServer, ADHPClient, ADHPPolicy, check_compliance

    # Server side
    server = ADHPServer(name="MyServer", config="adhp-config.json")

    # Client side
    client = ADHPClient(min_level="strict", require_compliance=["GDPR"])
    result = client.check("http://localhost:8000/mcp")
"""

from .checker import check_compliance
from .client import ADHPClient
from .config import load_policy, load_requirements
from .exceptions import (
    ADHPComplianceError,
    ADHPConfigError,
    ADHPConnectionError,
    ADHPError,
    ADHPValidationError,
)
from .models import (
    ADHPClientRequirements,
    ADHPPolicy,
    Check,
    ComplianceResult,
    ThirdParty,
    ThirdPartySharing,
)
from .server import ADHPServer

__version__ = "0.2.0"

__all__ = [
    "ADHPClient",
    "ADHPClientRequirements",
    "ADHPComplianceError",
    "ADHPConfigError",
    "ADHPConnectionError",
    "ADHPError",
    "ADHPPolicy",
    "ADHPServer",
    "ADHPValidationError",
    "Check",
    "ComplianceResult",
    "ThirdParty",
    "ThirdPartySharing",
    "check_compliance",
    "load_policy",
    "load_requirements",
]
