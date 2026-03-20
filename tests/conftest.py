"""Shared test fixtures for ADHP SDK tests."""

import pytest

from adhp.models import ADHPClientRequirements, ADHPPolicy, ThirdPartySharing


# ── Server policies ───────────────────────────────────────────────────


@pytest.fixture
def open_policy():
    return ADHPPolicy(
        level="open",
        training_opt_out=False,
        max_retention="unlimited",
        delegation_policy="unrestricted",
        compliance=[],
        processing_jurisdiction=[],
        storage_jurisdiction=[],
        log_jurisdiction=[],
    )


@pytest.fixture
def standard_policy():
    return ADHPPolicy(
        level="standard",
        training_opt_out=True,
        max_retention="session",
        session_ttl="4h",
        delegation_policy="same_or_higher",
        compliance=["GDPR"],
        processing_jurisdiction=["DE"],
        storage_jurisdiction=["DE"],
        log_jurisdiction=["DE"],
    )


@pytest.fixture
def strict_policy():
    return ADHPPolicy(
        level="strict",
        training_opt_out=True,
        third_party_opt_out=True,
        content_logging_opt_out=True,
        direct_marketing_opt_out=True,
        max_retention="request",
        delegation_policy="same_or_higher",
        compliance=["GDPR", "HIPAA"],
        pii_categories=["health", "identity", "email"],
        processing_jurisdiction=["DE"],
        storage_jurisdiction=["DE"],
        log_jurisdiction=["DE"],
    )


@pytest.fixture
def zero_trace_policy():
    return ADHPPolicy(
        level="zero-trace",
        training_opt_out=True,
        third_party_opt_out=True,
        content_logging_opt_out=True,
        direct_marketing_opt_out=True,
        scientific_usage_opt_in=False,
        max_retention="none",
        delegation_policy="none",
        compliance=["GDPR", "HIPAA", "AI_ACT_EU"],
        pii_categories=["email", "phone", "financial", "health", "identity", "location", "biometric"],
        processing_jurisdiction=["CH"],
        storage_jurisdiction=[],
        log_jurisdiction=[],
    )


@pytest.fixture
def eu_finance_policy():
    return ADHPPolicy(
        level="strict",
        training_opt_out=True,
        third_party_opt_out=True,
        content_logging_opt_out=True,
        direct_marketing_opt_out=True,
        max_retention="request",
        delegation_policy="same_or_higher",
        compliance=["GDPR", "AI_ACT_EU"],
        pii_categories=["email", "financial", "identity"],
        processing_jurisdiction=["DE", "FR"],
        storage_jurisdiction=["DE"],
        log_jurisdiction=["DE"],
    )


@pytest.fixture
def research_policy():
    return ADHPPolicy(
        level="standard",
        training_opt_out=True,
        direct_marketing_opt_out=True,
        scientific_usage_opt_in=True,
        max_retention="session",
        session_ttl="4h",
        delegation_policy="same_or_higher",
        compliance=["GDPR"],
        processing_jurisdiction=["DE"],
        storage_jurisdiction=["DE"],
        log_jurisdiction=["DE"],
    )


# ── Client requirements ──────────────────────────────────────────────


@pytest.fixture
def no_requirements():
    return ADHPClientRequirements()


@pytest.fixture
def strict_requirements():
    return ADHPClientRequirements(
        min_level="strict",
        require_compliance=["GDPR", "HIPAA"],
        accepted_jurisdictions=["DE", "FR"],
        require_training_opt_out=True,
        require_no_third_party=True,
        max_retention="request",
    )


@pytest.fixture
def gdpr_eu_requirements():
    return ADHPClientRequirements(
        min_level="standard",
        require_compliance=["GDPR"],
        accepted_jurisdictions=["DE", "FR", "NL", "BE", "AT", "IT", "ES"],
        require_training_opt_out=True,
    )
