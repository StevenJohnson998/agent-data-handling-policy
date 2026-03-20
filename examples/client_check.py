"""Client that connects to an MCP server and checks ADHP compliance."""

import sys

from adhp import ADHPClient

# Create a client with specific requirements
client = ADHPClient(
    min_level="strict",
    require_compliance=["GDPR"],
    accepted_jurisdictions=["DE", "FR"],
    require_training_opt_out=True,
    require_no_third_party=True,
    max_retention="24h",
)

# Check a server
url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/mcp"
print(f"Checking {url} ...")

result = client.check(url)

if result.compliant:
    print("\nPASS — Server meets all requirements\n")
else:
    print("\nFAIL — Server does NOT meet requirements\n")

for check in result.checks:
    icon = "PASS" if check.passed else "FAIL"
    print(f"  [{icon}] {check.name}: {check.reason}")
