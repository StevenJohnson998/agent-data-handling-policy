"""Gateway that filters MCP servers based on ADHP compliance.

Demonstrates how a gateway/orchestrator can check multiple servers
and only route to compliant ones.
"""

from adhp import ADHPClient, ADHPPolicy, check_compliance
from adhp.models import ADHPClientRequirements

# Gateway requirements: EU GDPR, minimum standard level
gateway_requirements = ADHPClientRequirements(
    min_level="standard",
    require_compliance=["GDPR"],
    accepted_jurisdictions=["DE", "FR", "NL", "BE", "AT", "IT", "ES"],
    require_training_opt_out=True,
)

# Simulated server policies (in production, these come from MCP initialize)
servers = {
    "FinanceAnalyzer": ADHPPolicy(
        level="strict",
        training_opt_out=True,
        third_party_opt_out=True,
        content_logging_opt_out=True,
        compliance=["GDPR", "AI_ACT_EU"],
        processing_jurisdiction=["DE"],
        storage_jurisdiction=["DE"],
        log_jurisdiction=["DE"],
        max_retention="request",
    ),
    "CheapLLM": ADHPPolicy(
        level="open",
        compliance=[],
        processing_jurisdiction=["US"],
    ),
    "EUTranslator": ADHPPolicy(
        level="standard",
        training_opt_out=True,
        compliance=["GDPR"],
        processing_jurisdiction=["NL"],
        storage_jurisdiction=["NL"],
        log_jurisdiction=["NL"],
        max_retention="session",
        session_ttl="4h",
    ),
}

# Filter servers
print("Gateway ADHP Filter")
print("=" * 50)
print(f"Requirements: min_level={gateway_requirements.min_level}, "
      f"compliance={gateway_requirements.require_compliance}\n")

compliant_servers = []
for name, policy in servers.items():
    result = check_compliance(gateway_requirements, policy)
    status = "PASS" if result.compliant else "FAIL"
    print(f"  [{status}] {name} (level={policy.level})")
    if not result.compliant:
        for c in result.checks:
            if not c.passed:
                print(f"         {c.name}: {c.reason}")
    else:
        compliant_servers.append(name)

print(f"\nCompliant servers: {', '.join(compliant_servers) or 'none'}")
print(f"Blocked servers: {', '.join(n for n in servers if n not in compliant_servers) or 'none'}")
