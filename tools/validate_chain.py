#!/usr/bin/env python3
"""
ADHP Delegation Chain Validator

Validates that delegation chains respect the caller's requested ADHP level.
Also validates individual agent manifests against ADHP rules.

Usage:
    python validate_chain.py                         # Run example scenarios
    python validate_chain.py --manifest FILE         # Validate a manifest file
    python validate_chain.py --chain FILE --level X  # Validate a chain from file
"""

import json
import sys
import os

# ADHP level hierarchy (0 = lowest, 4 = highest)
LEVELS = {
    "open": 0,
    "standard": 1,
    "sensitive": 2,
    "strict": 3,
    "zero-trace": 4
}

LEVEL_NAMES = {v: k for k, v in LEVELS.items()}


def level_value(level_str: str) -> int:
    """Convert level string to numeric value."""
    if level_str not in LEVELS:
        raise ValueError(f"Unknown ADHP level: '{level_str}'. Valid: {list(LEVELS.keys())}")
    return LEVELS[level_str]


def validate_chain(chain: list, caller_requires: str) -> dict:
    """
    Validate a delegation chain against the caller's required ADHP level.

    Args:
        chain: List of dicts with at least 'name' and 'level' keys.
        caller_requires: The ADHP level the caller requested (e.g., 'sensitive').

    Returns:
        dict with 'valid' (bool), 'reason' (str), and 'details' (list).
    """
    required_value = level_value(caller_requires)
    details = []
    all_valid = True
    failed_agent = None

    for i, agent in enumerate(chain):
        name = agent.get("name", f"Agent {i+1}")
        agent_level = agent.get("level", "open")
        agent_value = level_value(agent_level)

        # Check: Level 4 agents cannot delegate
        delegation_policy = agent.get("delegation_policy", "same_or_higher")
        is_zero_trace = agent_level == "zero-trace"
        has_next = i < len(chain) - 1

        if is_zero_trace and has_next:
            details.append({
                "agent": name,
                "level": agent_level,
                "status": "FAIL",
                "reason": "Level 4 (zero-trace) agents cannot delegate"
            })
            all_valid = False
            failed_agent = name
            break

        if delegation_policy == "none" and has_next:
            details.append({
                "agent": name,
                "level": agent_level,
                "status": "FAIL",
                "reason": f"Delegation policy is 'none' but attempts to delegate to {chain[i+1].get('name', 'next agent')}"
            })
            all_valid = False
            failed_agent = name
            break

        # Check: Agent level meets caller's requirement
        if agent_value < required_value:
            details.append({
                "agent": name,
                "level": agent_level,
                "status": "FAIL",
                "reason": f"Level {agent_value} ({agent_level}) is below caller's minimum Level {required_value} ({caller_requires})"
            })
            all_valid = False
            failed_agent = name
            break
        else:
            details.append({
                "agent": name,
                "level": agent_level,
                "status": "OK",
                "reason": f"Level {agent_value} ({agent_level}) meets Level {required_value} ({caller_requires})"
            })

    # Check third-party sharing in chain
    for agent in chain:
        tps = agent.get("third_party_sharing", {})
        if tps.get("enabled", False):
            parties = tps.get("parties", [])
            for party in parties:
                party_name = party.get("name", "Undisclosed")
                party_type = party.get("type", "undisclosed")
                party_level = party.get("adhp_level")

                if party_type == "undisclosed" or party_level is None:
                    effective_level = 0
                else:
                    effective_level = level_value(party_level)

                if effective_level < required_value:
                    details.append({
                        "agent": agent.get("name", "Unknown"),
                        "level": agent.get("level", "open"),
                        "status": "FAIL",
                        "reason": f"Third party '{party_name}' ({party_type}) has effective level {effective_level}, below caller's {required_value}"
                    })
                    all_valid = False
                    failed_agent = agent.get("name", "Unknown")

    if all_valid:
        reason = f"All agents meet caller's minimum level ({caller_requires})"
    else:
        reason = f"Chain invalid: {failed_agent} does not meet requirements"

    return {
        "valid": all_valid,
        "caller_requires": caller_requires,
        "chain_length": len(chain),
        "reason": reason,
        "details": details
    }


def validate_manifest(manifest: dict) -> dict:
    """
    Validate an ADHP manifest for internal consistency.

    Args:
        manifest: dict with 'data_handling' key containing ADHP properties.

    Returns:
        dict with 'valid' (bool) and 'issues' (list of strings).
    """
    dh = manifest.get("data_handling", manifest)
    issues = []
    level = dh.get("level", "open")

    # Level 4 constraints
    if level == "zero-trace":
        if dh.get("delegation_policy") != "none":
            issues.append("Level 4 (zero-trace) requires delegation_policy: 'none'")
        if dh.get("content_logging") is True:
            issues.append("Level 4 (zero-trace) requires content_logging: false")
        if dh.get("max_retention") != "none":
            issues.append("Level 4 (zero-trace) requires max_retention: 'none'")
        if dh.get("training_opt_out") is not True:
            issues.append("Level 4 (zero-trace) requires training_opt_out: true")
        if dh.get("execution_environment") in [None, "standard"]:
            issues.append("Level 4 (zero-trace) SHOULD declare execution_environment as 'TEE' or 'enclave' for credibility")

    # Level 3 constraints
    if level == "strict":
        if dh.get("content_logging") is True:
            issues.append("Level 3 (strict) requires content_logging: false")
        if dh.get("training_opt_out") is not True:
            issues.append("Level 3 (strict) requires training_opt_out: true")
        tps = dh.get("third_party_sharing", {})
        if tps.get("enabled") is True:
            issues.append("Level 3 (strict) requires third_party_sharing.enabled: false")

    # Level 2 constraints
    if level == "sensitive":
        if dh.get("training_opt_out") is not True:
            issues.append("Level 2 (sensitive) requires training_opt_out: true")
        if dh.get("output_sanitization") is not True:
            issues.append("Level 2 (sensitive) requires output_sanitization: true")

    # Level 1 constraints
    if level == "standard":
        if dh.get("training_opt_out") is not True:
            issues.append("Level 1 (standard) requires training_opt_out: true")

    # Session TTL required when max_retention is session
    if dh.get("max_retention") == "session" and not dh.get("session_ttl"):
        issues.append("max_retention 'session' requires session_ttl to be specified")

    # Retention days required when max_retention is custom
    if dh.get("max_retention") == "custom" and dh.get("retention_days") is None:
        issues.append("max_retention 'custom' requires retention_days to be specified")

    # Third-party consistency
    tps = dh.get("third_party_sharing", {})
    if tps.get("enabled") is False and tps.get("parties") and len(tps["parties"]) > 0:
        issues.append("third_party_sharing.enabled is false but parties are listed")

    if tps.get("enabled") is True:
        parties = tps.get("parties", [])
        if not parties:
            issues.append("third_party_sharing.enabled is true but no parties are declared (treated as undisclosed = Level 0)")
        for party in parties:
            if party.get("type") == "undisclosed":
                issues.append(f"Undisclosed third party detected -- effective level drops to 0")

    return {
        "valid": len(issues) == 0,
        "level": level,
        "issues": issues
    }


def print_result(result: dict, title: str = ""):
    """Pretty-print a validation result."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")

    status = "VALID" if result["valid"] else "INVALID"
    icon = "[OK]" if result["valid"] else "[FAIL]"

    print(f"\n  {icon} {status}")

    if "caller_requires" in result:
        print(f"  Caller requires: {result['caller_requires']}")
        print(f"  Chain length: {result['chain_length']}")

    if "reason" in result:
        print(f"  Reason: {result['reason']}")

    if "details" in result:
        print(f"\n  Chain:")
        for i, d in enumerate(result["details"]):
            icon = "  [OK]" if d["status"] == "OK" else "  [!!]"
            print(f"    {icon} {d['agent']} ({d['level']}): {d['reason']}")

    if "issues" in result:
        if result["issues"]:
            print(f"\n  Issues:")
            for issue in result["issues"]:
                print(f"    [!!] {issue}")
        else:
            print(f"\n  No issues found.")

    print()


def run_examples():
    """Run built-in example scenarios."""

    print("\n" + "="*60)
    print("  ADHP Delegation Chain Validator -- Example Scenarios")
    print("="*60)

    # Scenario 1: Valid chain
    print_result(
        validate_chain(
            chain=[
                {"name": "MedAnalyzer", "level": "strict"},
                {"name": "OCR-Service", "level": "sensitive"},
                {"name": "DataCleaner", "level": "strict"}
            ],
            caller_requires="sensitive"
        ),
        "Scenario 1: Medical data analysis (caller requires: sensitive)"
    )

    # Scenario 2: Weak link
    print_result(
        validate_chain(
            chain=[
                {"name": "LegalReview Pro", "level": "strict"},
                {"name": "BudgetTranslator", "level": "standard"},
                {"name": "ClauseAnalyzer", "level": "strict"}
            ],
            caller_requires="strict"
        ),
        "Scenario 2: Legal review with weak link (caller requires: strict)"
    )

    # Scenario 3: High agent, low request
    print_result(
        validate_chain(
            chain=[
                {"name": "SecureAgent", "level": "strict"},
                {"name": "BasicHelper", "level": "standard"}
            ],
            caller_requires="standard"
        ),
        "Scenario 3: Strict agent delegating to standard (caller requires: standard)"
    )

    # Scenario 4: Zero-trace tries to delegate
    print_result(
        validate_chain(
            chain=[
                {"name": "TopSecret Agent", "level": "zero-trace"},
                {"name": "Helper", "level": "strict"}
            ],
            caller_requires="strict"
        ),
        "Scenario 4: Zero-trace agent tries to delegate (not allowed)"
    )

    # Scenario 5: Third-party breaks chain
    print_result(
        validate_chain(
            chain=[
                {
                    "name": "SmartAssistant",
                    "level": "sensitive",
                    "third_party_sharing": {
                        "enabled": True,
                        "parties": [
                            {
                                "name": "Analytics Corp",
                                "type": "undisclosed",
                                "purpose": "analytics",
                                "adhp_level": None
                            }
                        ]
                    }
                }
            ],
            caller_requires="sensitive"
        ),
        "Scenario 5: Agent with undisclosed third party (caller requires: sensitive)"
    )

    # Scenario 6: Valid chain with declared third party
    print_result(
        validate_chain(
            chain=[
                {
                    "name": "FinanceBot",
                    "level": "strict",
                    "third_party_sharing": {
                        "enabled": True,
                        "parties": [
                            {
                                "name": "AuditAgent",
                                "type": "agent",
                                "purpose": "subprocessing",
                                "adhp_level": "strict",
                                "registry_id": "abc-123"
                            }
                        ]
                    }
                }
            ],
            caller_requires="strict"
        ),
        "Scenario 6: Agent with declared strict third party (caller requires: strict)"
    )

    # Manifest validation
    print("\n" + "="*60)
    print("  Manifest Validation Examples")
    print("="*60)

    # Valid manifest
    print_result(
        validate_manifest({
            "data_handling": {
                "level": "strict",
                "training_opt_out": True,
                "max_retention": "request",
                "content_logging": False,
                "delegation_policy": "same_or_higher",
                "output_sanitization": True,
                "third_party_sharing": {"enabled": False}
            }
        }),
        "Manifest 1: Valid strict agent"
    )

    # Invalid: zero-trace with delegation
    print_result(
        validate_manifest({
            "data_handling": {
                "level": "zero-trace",
                "training_opt_out": True,
                "max_retention": "none",
                "content_logging": False,
                "delegation_policy": "same_or_higher",
                "output_sanitization": True,
                "third_party_sharing": {"enabled": False}
            }
        }),
        "Manifest 2: Zero-trace with delegation (should fail)"
    )

    # Invalid: strict with third-party sharing
    print_result(
        validate_manifest({
            "data_handling": {
                "level": "strict",
                "training_opt_out": True,
                "max_retention": "request",
                "content_logging": False,
                "delegation_policy": "same_or_higher",
                "output_sanitization": True,
                "third_party_sharing": {
                    "enabled": True,
                    "parties": [
                        {"type": "undisclosed", "purpose": "analytics"}
                    ]
                }
            }
        }),
        "Manifest 3: Strict agent with undisclosed third party (should fail)"
    )


def main():
    if len(sys.argv) == 1:
        run_examples()
        return

    if "--manifest" in sys.argv:
        idx = sys.argv.index("--manifest")
        if idx + 1 >= len(sys.argv):
            print("Error: --manifest requires a file path")
            sys.exit(1)
        filepath = sys.argv[idx + 1]
        with open(filepath) as f:
            manifest = json.load(f)
        result = validate_manifest(manifest)
        print_result(result, f"Manifest: {os.path.basename(filepath)}")
        sys.exit(0 if result["valid"] else 1)

    if "--chain" in sys.argv:
        idx = sys.argv.index("--chain")
        level_idx = sys.argv.index("--level") if "--level" in sys.argv else None
        if idx + 1 >= len(sys.argv):
            print("Error: --chain requires a file path")
            sys.exit(1)
        if level_idx is None or level_idx + 1 >= len(sys.argv):
            print("Error: --chain requires --level (e.g., --level strict)")
            sys.exit(1)
        filepath = sys.argv[idx + 1]
        caller_level = sys.argv[level_idx + 1]
        with open(filepath) as f:
            chain = json.load(f)
        result = validate_chain(chain, caller_level)
        print_result(result, f"Chain: {os.path.basename(filepath)}")
        sys.exit(0 if result["valid"] else 1)

    print("Usage:")
    print("  python validate_chain.py                         # Run examples")
    print("  python validate_chain.py --manifest FILE         # Validate manifest")
    print("  python validate_chain.py --chain FILE --level X  # Validate chain")


if __name__ == "__main__":
    main()
