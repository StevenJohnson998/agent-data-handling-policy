"""Full test coverage for the compliance checker — 18+ scenarios."""

import pytest

from adhp.checker import check_compliance
from adhp.models import (
    ADHPClientRequirements,
    ADHPPolicy,
    ThirdPartySharing,
)


# ── 1. Level checks ──────────────────────────────────────────────────


class TestLevelCheck:
    def test_server_level_gte_client_passes(self, strict_policy):
        """Scenario 1: Server level >= client level → PASS."""
        req = ADHPClientRequirements(min_level="standard")
        result = check_compliance(req, strict_policy)
        level_check = _find_check(result, "level")
        assert level_check.passed

    def test_server_level_lt_client_fails(self, open_policy):
        """Scenario 2: Server level < client level → FAIL."""
        req = ADHPClientRequirements(min_level="strict")
        result = check_compliance(req, open_policy)
        level_check = _find_check(result, "level")
        assert not level_check.passed
        assert not result.compliant

    def test_exact_level_match_passes(self, strict_policy):
        """Exact level match passes."""
        req = ADHPClientRequirements(min_level="strict")
        result = check_compliance(req, strict_policy)
        level_check = _find_check(result, "level")
        assert level_check.passed


# ── 2. Compliance framework checks ───────────────────────────────────


class TestComplianceCheck:
    def test_all_required_compliance_present_passes(self, strict_policy):
        """Scenario 3: Server has all required compliance tags → PASS."""
        req = ADHPClientRequirements(require_compliance=["GDPR", "HIPAA"])
        result = check_compliance(req, strict_policy)
        comp_check = _find_check(result, "compliance")
        assert comp_check.passed

    def test_missing_compliance_tag_fails(self, strict_policy):
        """Scenario 4: Server missing one compliance tag → FAIL."""
        req = ADHPClientRequirements(require_compliance=["GDPR", "CCPA"])
        result = check_compliance(req, strict_policy)
        comp_check = _find_check(result, "compliance")
        assert not comp_check.passed
        assert "CCPA" in comp_check.reason

    def test_no_compliance_requirement_passes(self, open_policy):
        """No compliance requirement means check passes."""
        req = ADHPClientRequirements()
        result = check_compliance(req, open_policy)
        comp_check = _find_check(result, "compliance")
        assert comp_check.passed


# ── 3. Jurisdiction checks ───────────────────────────────────────────


class TestJurisdictionCheck:
    def test_all_server_jurisdictions_within_accepted_passes(self, strict_policy):
        """Scenario 5: All server jurisdictions within client accepted list → PASS."""
        req = ADHPClientRequirements(accepted_jurisdictions=["DE", "FR"])
        result = check_compliance(req, strict_policy)
        jur_check = _find_check(result, "jurisdiction")
        assert jur_check.passed

    def test_server_jurisdiction_outside_client_list_fails(self, eu_finance_policy):
        """Scenario 6: One server jurisdiction outside client list → FAIL."""
        req = ADHPClientRequirements(accepted_jurisdictions=["DE"])
        # eu_finance_policy has processing in DE + FR, so FR is outside
        result = check_compliance(req, eu_finance_policy)
        jur_check = _find_check(result, "jurisdiction")
        assert not jur_check.passed
        assert "FR" in jur_check.reason

    def test_server_undeclared_jurisdiction_with_client_requirement_fails(self):
        """Scenario 7: Server jurisdiction undeclared + client has requirements → FAIL."""
        policy = ADHPPolicy(
            level="standard",
            processing_jurisdiction=[],
            storage_jurisdiction=[],
            log_jurisdiction=[],
        )
        req = ADHPClientRequirements(accepted_jurisdictions=["DE"])
        result = check_compliance(req, policy)
        jur_check = _find_check(result, "jurisdiction")
        assert not jur_check.passed
        assert "no jurisdictions" in jur_check.reason.lower()

    def test_no_jurisdiction_requirements_passes(self, open_policy):
        """Scenario 8: Client no jurisdiction requirements + server undeclared → PASS."""
        req = ADHPClientRequirements()
        result = check_compliance(req, open_policy)
        jur_check = _find_check(result, "jurisdiction")
        assert jur_check.passed


# ── 4. Training opt-out checks ───────────────────────────────────────


class TestTrainingCheck:
    def test_training_opt_out_required_and_declared_passes(self, strict_policy):
        """Scenario 9: Training opt-out required + server declares true → PASS."""
        req = ADHPClientRequirements(require_training_opt_out=True)
        result = check_compliance(req, strict_policy)
        train_check = _find_check(result, "training")
        assert train_check.passed

    def test_training_opt_out_required_server_false_fails(self, open_policy):
        """Scenario 10: Training opt-out required + server declares false → FAIL."""
        req = ADHPClientRequirements(require_training_opt_out=True)
        result = check_compliance(req, open_policy)
        train_check = _find_check(result, "training")
        assert not train_check.passed

    def test_training_opt_out_required_server_default_fails(self):
        """Scenario 11: Training opt-out required + server doesn't declare → FAIL (default=false)."""
        policy = ADHPPolicy(level="open")
        req = ADHPClientRequirements(require_training_opt_out=True)
        result = check_compliance(req, policy)
        train_check = _find_check(result, "training")
        assert not train_check.passed


# ── 5. Third-party sharing checks ────────────────────────────────────


class TestThirdPartyCheck:
    def test_third_party_forbidden_server_disabled_passes(self):
        """Scenario 12: Third-party sharing forbidden + server disabled → PASS."""
        policy = ADHPPolicy(
            level="strict",
            training_opt_out=True,
            third_party_opt_out=True,
            content_logging_opt_out=True,
        )
        req = ADHPClientRequirements(require_no_third_party=True)
        result = check_compliance(req, policy)
        tp_check = _find_check(result, "third_party")
        assert tp_check.passed

    def test_third_party_forbidden_server_enabled_fails(self, open_policy):
        """Scenario 13: Third-party sharing forbidden + server enabled → FAIL."""
        req = ADHPClientRequirements(require_no_third_party=True)
        result = check_compliance(req, open_policy)
        tp_check = _find_check(result, "third_party")
        assert not tp_check.passed

    def test_third_party_sharing_object_disabled_passes(self):
        """Third-party check passes when third_party_sharing.enabled=false."""
        policy = ADHPPolicy(
            level="standard",
            third_party_sharing=ThirdPartySharing(enabled=False),
        )
        req = ADHPClientRequirements(require_no_third_party=True)
        result = check_compliance(req, policy)
        tp_check = _find_check(result, "third_party")
        assert tp_check.passed


# ── 6. Retention checks ──────────────────────────────────────────────


class TestRetentionCheck:
    def test_server_retention_within_limit_passes(self):
        """Scenario 14: Client max '24h' + server 'request' → PASS."""
        policy = ADHPPolicy(level="standard", max_retention="request")
        req = ADHPClientRequirements(max_retention="24h")
        result = check_compliance(req, policy)
        ret_check = _find_check(result, "retention")
        assert ret_check.passed

    def test_server_retention_exceeds_limit_fails(self):
        """Scenario 15: Client max '24h' + server '30d' → FAIL."""
        policy = ADHPPolicy(level="standard", max_retention="30d")
        req = ADHPClientRequirements(max_retention="24h")
        result = check_compliance(req, policy)
        ret_check = _find_check(result, "retention")
        assert not ret_check.passed

    def test_no_retention_requirement_passes(self, open_policy):
        """No retention requirement means check passes."""
        req = ADHPClientRequirements()
        result = check_compliance(req, open_policy)
        ret_check = _find_check(result, "retention")
        assert ret_check.passed


# ── 7. Direct marketing checks ──────────────────────────────────────


class TestDirectMarketingCheck:
    def test_direct_marketing_opt_out_required_and_declared_passes(self, strict_policy):
        """Direct marketing opt-out required + server declares true → PASS."""
        req = ADHPClientRequirements(require_direct_marketing_opt_out=True)
        result = check_compliance(req, strict_policy)
        dm_check = _find_check(result, "direct_marketing")
        assert dm_check.passed

    def test_direct_marketing_opt_out_required_server_false_fails(self, open_policy):
        """Direct marketing opt-out required + server doesn't opt out → FAIL."""
        req = ADHPClientRequirements(require_direct_marketing_opt_out=True)
        result = check_compliance(req, open_policy)
        dm_check = _find_check(result, "direct_marketing")
        assert not dm_check.passed

    def test_direct_marketing_no_requirement_passes(self, open_policy):
        """No direct marketing requirement → always PASS."""
        req = ADHPClientRequirements()
        result = check_compliance(req, open_policy)
        dm_check = _find_check(result, "direct_marketing")
        assert dm_check.passed

    def test_direct_marketing_default_false_fails(self):
        """Default (undeclared) = False, fail-closed."""
        policy = ADHPPolicy(level="standard")
        req = ADHPClientRequirements(require_direct_marketing_opt_out=True)
        result = check_compliance(req, policy)
        dm_check = _find_check(result, "direct_marketing")
        assert not dm_check.passed


# ── 8. Scientific usage checks ──────────────────────────────────────


class TestScientificUsageCheck:
    def test_server_declares_scientific_client_consents_passes(self, research_policy):
        """Server declares scientific usage + client consents → PASS."""
        req = ADHPClientRequirements(allow_scientific_usage=True)
        result = check_compliance(req, research_policy)
        sci_check = _find_check(result, "scientific_usage")
        assert sci_check.passed

    def test_server_declares_scientific_client_does_not_consent_fails(self, research_policy):
        """Server declares scientific usage + client does NOT consent → FAIL."""
        req = ADHPClientRequirements(allow_scientific_usage=False)
        result = check_compliance(req, research_policy)
        sci_check = _find_check(result, "scientific_usage")
        assert not sci_check.passed
        assert "not consented" in sci_check.reason

    def test_server_no_scientific_client_no_consent_passes(self, strict_policy):
        """Server doesn't declare scientific + client doesn't consent → PASS (nothing to consent to)."""
        req = ADHPClientRequirements(allow_scientific_usage=False)
        result = check_compliance(req, strict_policy)
        sci_check = _find_check(result, "scientific_usage")
        assert sci_check.passed

    def test_server_no_scientific_client_consents_passes(self, strict_policy):
        """Server doesn't declare scientific + client consents → PASS (consent given but not needed)."""
        req = ADHPClientRequirements(allow_scientific_usage=True)
        result = check_compliance(req, strict_policy)
        sci_check = _find_check(result, "scientific_usage")
        assert sci_check.passed


# ── 10. Multiple requirements + edge cases ───────────────────────────


class TestMultipleRequirements:
    def test_multiple_requirements_one_fails(self, strict_policy):
        """Scenario 16: Multiple simultaneous requirements, one fails → overall FAIL."""
        req = ADHPClientRequirements(
            min_level="strict",
            require_compliance=["GDPR", "HIPAA"],
            accepted_jurisdictions=["US"],  # Will fail — server is DE
            require_training_opt_out=True,
        )
        result = check_compliance(req, strict_policy)
        assert not result.compliant
        jur_check = _find_check(result, "jurisdiction")
        assert not jur_check.passed
        # Other checks should still pass
        level_check = _find_check(result, "level")
        assert level_check.passed
        comp_check = _find_check(result, "compliance")
        assert comp_check.passed

    def test_no_requirements_always_passes(self, open_policy):
        """Scenario 17: No client requirements → PASS (everything passes)."""
        req = ADHPClientRequirements()
        result = check_compliance(req, open_policy)
        assert result.compliant

    def test_no_policy_with_requirements_fails(self):
        """Scenario 18: Server with no ADHP declaration → FAIL if client has ANY requirements."""
        req = ADHPClientRequirements(min_level="standard")
        result = check_compliance(req, None)
        assert not result.compliant

    def test_no_policy_no_requirements_passes(self):
        """No policy + no requirements = PASS."""
        req = ADHPClientRequirements()
        result = check_compliance(req, None)
        assert result.compliant

    def test_no_policy_with_direct_marketing_requirement_fails(self):
        """No policy + direct marketing opt-out required → FAIL."""
        req = ADHPClientRequirements(require_direct_marketing_opt_out=True)
        result = check_compliance(req, None)
        assert not result.compliant


# ── 11. Dict input ───────────────────────────────────────────────────


class TestDictInput:
    def test_policy_as_dict(self):
        """check_compliance accepts a raw dict as the policy."""
        policy_dict = {
            "level": "strict",
            "training_opt_out": True,
            "third_party_opt_out": True,
            "content_logging_opt_out": True,
            "compliance": ["GDPR"],
            "processing_jurisdiction": ["DE"],
            "storage_jurisdiction": ["DE"],
            "log_jurisdiction": ["DE"],
            "max_retention": "request",
        }
        req = ADHPClientRequirements(
            min_level="standard",
            require_compliance=["GDPR"],
            accepted_jurisdictions=["DE"],
        )
        result = check_compliance(req, policy_dict)
        assert result.compliant


# ── Helpers ───────────────────────────────────────────────────────────


def _find_check(result, name: str):
    """Find a check by name in a ComplianceResult."""
    for c in result.checks:
        if c.name == name:
            return c
    raise AssertionError(f"Check '{name}' not found in result: {[c.name for c in result.checks]}")
