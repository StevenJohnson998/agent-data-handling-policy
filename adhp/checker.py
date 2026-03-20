"""Core compliance checking logic — pure functions, no I/O."""

from __future__ import annotations

from .models import (
    ADHPClientRequirements,
    ADHPPolicy,
    Check,
    ComplianceResult,
    LEVEL_ORDER,
    RETENTION_ORDER,
)


def check_compliance(
    requirements: ADHPClientRequirements,
    policy: ADHPPolicy | dict | None,
) -> ComplianceResult:
    """Check whether a server's ADHP policy meets client requirements.

    Args:
        requirements: What the client/gateway requires.
        policy: The server's ADHP declaration. Can be an ADHPPolicy, a raw dict,
                or None (no declaration).

    Returns:
        ComplianceResult with overall pass/fail and individual check details.
    """
    checks: list[Check] = []

    # Handle missing policy
    if policy is None:
        return _fail_no_policy(requirements)

    # Normalise dict → ADHPPolicy
    if isinstance(policy, dict):
        policy = ADHPPolicy(**policy)

    # 1. Level check
    checks.append(_check_level(requirements, policy))

    # 2. Compliance frameworks
    checks.append(_check_compliance_frameworks(requirements, policy))

    # 3. Jurisdiction (processing, storage, log)
    checks.append(_check_jurisdictions(requirements, policy))

    # 4. Training opt-out
    checks.append(_check_training(requirements, policy))

    # 5. Third-party sharing
    checks.append(_check_third_party(requirements, policy))

    # 6. Retention
    checks.append(_check_retention(requirements, policy))

    # 7. Content logging
    checks.append(_check_content_logging(requirements, policy))

    # 8. Direct marketing
    checks.append(_check_direct_marketing(requirements, policy))

    # 9. Scientific usage
    checks.append(_check_scientific_usage(requirements, policy))

    compliant = all(c.passed for c in checks)
    return ComplianceResult(compliant=compliant, checks=checks)


# ── Individual checks ─────────────────────────────────────────────────


def _check_level(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    server_val = LEVEL_ORDER[pol.level]
    client_val = LEVEL_ORDER[req.min_level]
    if server_val >= client_val:
        return Check(
            name="level",
            passed=True,
            reason=f"Server level '{pol.level}' ({server_val}) >= required '{req.min_level}' ({client_val})",
        )
    return Check(
        name="level",
        passed=False,
        reason=f"Server level '{pol.level}' ({server_val}) < required '{req.min_level}' ({client_val})",
    )


def _check_compliance_frameworks(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if not req.require_compliance:
        return Check(name="compliance", passed=True, reason="No compliance requirements specified")

    required = set(req.require_compliance)
    declared = set(pol.compliance)
    missing = required - declared
    if not missing:
        return Check(
            name="compliance",
            passed=True,
            reason=f"Server declares all required frameworks: {', '.join(sorted(required))}",
        )
    return Check(
        name="compliance",
        passed=False,
        reason=f"Server missing required compliance: {', '.join(sorted(missing))} (declares: {', '.join(sorted(declared)) or 'none'})",
    )


def _check_jurisdictions(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if not req.accepted_jurisdictions:
        return Check(name="jurisdiction", passed=True, reason="No jurisdiction requirements specified")

    accepted = set(req.accepted_jurisdictions)
    # Collect all server-declared jurisdictions
    all_server_jurisdictions: set[str] = set()
    all_server_jurisdictions.update(pol.processing_jurisdiction)
    all_server_jurisdictions.update(pol.storage_jurisdiction)
    all_server_jurisdictions.update(pol.log_jurisdiction)

    # If server declares nothing, fail — undeclared = no guarantee
    if not all_server_jurisdictions:
        return Check(
            name="jurisdiction",
            passed=False,
            reason=f"Server declares no jurisdictions; client requires data stay within {', '.join(sorted(accepted))}",
        )

    outside = all_server_jurisdictions - accepted
    if not outside:
        return Check(
            name="jurisdiction",
            passed=True,
            reason=f"All server jurisdictions ({', '.join(sorted(all_server_jurisdictions))}) within accepted list",
        )
    return Check(
        name="jurisdiction",
        passed=False,
        reason=f"Server jurisdictions {', '.join(sorted(outside))} outside accepted list ({', '.join(sorted(accepted))})",
    )


def _check_training(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if not req.require_training_opt_out:
        return Check(name="training", passed=True, reason="No training opt-out requirement")

    if pol.training_opt_out:
        return Check(name="training", passed=True, reason="Server declares training_opt_out: true")
    return Check(
        name="training",
        passed=False,
        reason="Server does not declare training_opt_out: true (client requires it)",
    )


def _check_third_party(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if not req.require_no_third_party:
        return Check(name="third_party", passed=True, reason="No third-party restriction required")

    # Check the simple boolean flag first
    if pol.third_party_opt_out:
        return Check(name="third_party", passed=True, reason="Server declares third_party_opt_out: true")

    # Also check the detailed third_party_sharing object
    if pol.third_party_sharing is not None and not pol.third_party_sharing.enabled:
        return Check(
            name="third_party",
            passed=True,
            reason="Server declares third_party_sharing.enabled: false",
        )

    return Check(
        name="third_party",
        passed=False,
        reason="Server allows third-party sharing (client requires it disabled)",
    )


def _check_retention(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if req.max_retention is None:
        return Check(name="retention", passed=True, reason="No retention requirement specified")

    client_max = RETENTION_ORDER.get(req.max_retention, 99)
    server_val = RETENTION_ORDER.get(pol.max_retention, 99)

    if server_val <= client_max:
        return Check(
            name="retention",
            passed=True,
            reason=f"Server retention '{pol.max_retention}' <= client max '{req.max_retention}'",
        )
    return Check(
        name="retention",
        passed=False,
        reason=f"Server retention '{pol.max_retention}' exceeds client max '{req.max_retention}'",
    )


def _check_content_logging(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if not req.require_content_logging_opt_out:
        return Check(name="content_logging", passed=True, reason="No content logging opt-out requirement")

    if pol.content_logging_opt_out:
        return Check(
            name="content_logging",
            passed=True,
            reason="Server declares content_logging_opt_out: true",
        )
    return Check(
        name="content_logging",
        passed=False,
        reason="Server does not declare content_logging_opt_out: true (client requires it)",
    )


def _check_direct_marketing(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if not req.require_direct_marketing_opt_out:
        return Check(name="direct_marketing", passed=True, reason="No direct marketing opt-out requirement")

    if pol.direct_marketing_opt_out:
        return Check(
            name="direct_marketing",
            passed=True,
            reason="Server declares direct_marketing_opt_out: true",
        )
    return Check(
        name="direct_marketing",
        passed=False,
        reason="Server does not declare direct_marketing_opt_out: true (client requires it)",
    )


def _check_scientific_usage(req: ADHPClientRequirements, pol: ADHPPolicy) -> Check:
    if not req.allow_scientific_usage:
        # Client has NOT consented — if server declares scientific usage, fail
        if pol.scientific_usage_opt_in:
            return Check(
                name="scientific_usage",
                passed=False,
                reason="Server declares scientific_usage_opt_in: true but client has not consented",
            )
        return Check(
            name="scientific_usage",
            passed=True,
            reason="Server does not declare scientific usage; no consent needed",
        )
    # Client consents to scientific usage — always passes
    return Check(
        name="scientific_usage",
        passed=True,
        reason="Client allows scientific usage",
    )


# ── Missing policy handler ───────────────────────────────────────────


def _fail_no_policy(req: ADHPClientRequirements) -> ComplianceResult:
    """When server has no ADHP declaration at all."""
    # If client has no requirements, a missing policy is fine (assume open)
    has_any_requirement = (
        req.min_level != "open"
        or req.require_compliance
        or req.accepted_jurisdictions
        or req.require_training_opt_out
        or req.require_no_third_party
        or req.max_retention is not None
        or req.require_content_logging_opt_out
        or req.require_direct_marketing_opt_out
    )

    if not has_any_requirement:
        return ComplianceResult(
            compliant=True,
            checks=[
                Check(
                    name="policy_present",
                    passed=True,
                    reason="No ADHP declaration, but client has no requirements",
                )
            ],
        )

    return ComplianceResult(
        compliant=False,
        checks=[
            Check(
                name="policy_present",
                passed=False,
                reason="Server has no ADHP declaration; client has requirements that cannot be verified",
            )
        ],
    )
