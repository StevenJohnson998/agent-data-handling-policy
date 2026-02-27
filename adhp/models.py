"""Pydantic models for all ADHP v0.2 fields."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ── Enums as Literal types ────────────────────────────────────────────

ADHPLevel = Literal["open", "standard", "sensitive", "strict", "zero-trace"]
RetentionPeriod = Literal[
    "none", "request", "session", "24h", "7d", "30d", "custom", "unlimited"
]
DelegationPolicy = Literal["none", "same_or_higher", "unrestricted"]
ExecutionEnvironment = Literal["standard", "containerized", "TEE", "enclave"]
SessionTTL = Literal["1h", "4h", "8h", "24h"]
PIICategory = Literal[
    "email", "phone", "financial", "health", "identity", "location", "biometric"
]
SharingPurpose = Literal[
    "analytics", "advertising", "improvement", "subprocessing", "legal", "resale"
]
PartyType = Literal["agent", "non_agent", "undisclosed"]

# ── Numeric ordering maps ─────────────────────────────────────────────

LEVEL_ORDER: dict[str, int] = {
    "open": 0,
    "standard": 1,
    "sensitive": 2,
    "strict": 3,
    "zero-trace": 4,
}

RETENTION_ORDER: dict[str, int] = {
    "none": 0,
    "request": 1,
    "session": 2,
    "24h": 3,
    "7d": 4,
    "30d": 5,
    "custom": 6,
    "unlimited": 7,
}


# ── Third-party sharing models ────────────────────────────────────────


class ThirdParty(BaseModel):
    """A single third-party entity that may receive data."""

    name: Optional[str] = None
    type: PartyType
    purpose: SharingPurpose
    adhp_level: Optional[ADHPLevel] = None


class ThirdPartySharing(BaseModel):
    """Detailed third-party sharing configuration."""

    enabled: bool = True
    purpose: list[SharingPurpose] = Field(default_factory=list)
    sanitized: bool = False
    parties_disclosed: bool = False
    opt_out_available: bool = False
    parties: list[ThirdParty] = Field(default_factory=list)


# ── Main ADHP Policy model ────────────────────────────────────────────


class ADHPPolicy(BaseModel):
    """Full ADHP v0.2 policy declaration — server side."""

    level: ADHPLevel
    training_opt_out: bool = False
    third_party_opt_out: bool = False
    content_logging_opt_out: bool = False
    output_sanitization_opt_in: bool = False
    max_retention: RetentionPeriod = "unlimited"
    retention_days: Optional[int] = Field(default=None, ge=0)
    session_ttl: Optional[SessionTTL] = None
    delegation_policy: DelegationPolicy = "unrestricted"
    compliance: list[str] = Field(default_factory=list)
    pii_categories: list[PIICategory] = Field(default_factory=list)
    processing_jurisdiction: list[str] = Field(default_factory=list)
    storage_jurisdiction: list[str] = Field(default_factory=list)
    log_jurisdiction: list[str] = Field(default_factory=list)
    execution_environment: ExecutionEnvironment = "standard"
    certification: Optional[str] = None
    third_party_sharing: Optional[ThirdPartySharing] = None

    @model_validator(mode="after")
    def _check_conditional_fields(self) -> "ADHPPolicy":
        if self.max_retention == "custom" and self.retention_days is None:
            raise ValueError("retention_days is required when max_retention is 'custom'")
        if self.max_retention == "session" and self.session_ttl is None:
            raise ValueError("session_ttl is required when max_retention is 'session'")
        return self

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for MCP capabilities."""
        return self.model_dump(exclude_none=True, exclude_defaults=False)


# ── Client requirements model ─────────────────────────────────────────


class ADHPClientRequirements(BaseModel):
    """What a client/gateway requires from a server's ADHP policy."""

    min_level: ADHPLevel = "open"
    require_compliance: list[str] = Field(default_factory=list)
    accepted_jurisdictions: list[str] = Field(default_factory=list)
    require_training_opt_out: bool = False
    require_no_third_party: bool = False
    max_retention: Optional[RetentionPeriod] = None
    require_content_logging_opt_out: bool = False
    require_dpa_verification: bool = False  # TODO: v0.4 DPA verification layer


# ── Compliance result models ──────────────────────────────────────────


class Check(BaseModel):
    """A single compliance check result."""

    name: str
    passed: bool
    reason: str


class ComplianceResult(BaseModel):
    """Overall result of a compliance check."""

    compliant: bool
    checks: list[Check] = Field(default_factory=list)
