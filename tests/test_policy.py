"""Unit tests for policy parsing, config loading, and validation."""

import json
import os
import tempfile

import pytest

from adhp.config import load_policy, load_requirements
from adhp.exceptions import ADHPConfigError
from adhp.models import ADHPClientRequirements, ADHPPolicy, ThirdPartySharing
from adhp.schema import validate_policy_dict, validate_policy_file


# ── Model construction ────────────────────────────────────────────────


class TestADHPPolicy:
    def test_minimal_policy(self):
        p = ADHPPolicy(level="open")
        assert p.level == "open"
        assert p.training_opt_out is False
        assert p.max_retention == "unlimited"

    def test_full_policy(self):
        p = ADHPPolicy(
            level="strict",
            training_opt_out=True,
            third_party_opt_out=True,
            content_logging_opt_out=True,
            output_sanitization_opt_in=True,
            max_retention="request",
            delegation_policy="same_or_higher",
            compliance=["GDPR", "HIPAA"],
            pii_categories=["email", "health"],
            processing_jurisdiction=["DE"],
            storage_jurisdiction=["DE"],
            log_jurisdiction=["DE"],
            execution_environment="TEE",
            third_party_sharing=ThirdPartySharing(enabled=False),
        )
        assert p.level == "strict"
        assert p.compliance == ["GDPR", "HIPAA"]
        assert p.third_party_sharing.enabled is False

    def test_to_dict(self):
        p = ADHPPolicy(level="standard", compliance=["GDPR"])
        d = p.to_dict()
        assert d["level"] == "standard"
        assert d["compliance"] == ["GDPR"]
        assert isinstance(d, dict)

    def test_custom_retention_requires_days(self):
        with pytest.raises(ValueError, match="retention_days"):
            ADHPPolicy(level="standard", max_retention="custom")

    def test_custom_retention_with_days(self):
        p = ADHPPolicy(level="standard", max_retention="custom", retention_days=90)
        assert p.retention_days == 90

    def test_session_retention_requires_ttl(self):
        with pytest.raises(ValueError, match="session_ttl"):
            ADHPPolicy(level="standard", max_retention="session")

    def test_session_retention_with_ttl(self):
        p = ADHPPolicy(level="standard", max_retention="session", session_ttl="4h")
        assert p.session_ttl == "4h"

    def test_invalid_level_rejected(self):
        with pytest.raises(Exception):
            ADHPPolicy(level="invalid")


class TestClientRequirements:
    def test_default_requirements(self):
        r = ADHPClientRequirements()
        assert r.min_level == "open"
        assert r.require_compliance == []
        assert r.require_no_third_party is False

    def test_full_requirements(self):
        r = ADHPClientRequirements(
            min_level="strict",
            require_compliance=["GDPR"],
            accepted_jurisdictions=["DE"],
            require_training_opt_out=True,
            require_no_third_party=True,
            max_retention="24h",
        )
        assert r.min_level == "strict"
        assert r.max_retention == "24h"


# ── Config loading ────────────────────────────────────────────────────


class TestConfigLoading:
    def test_load_policy_from_dict(self):
        p = load_policy({"level": "standard"})
        assert isinstance(p, ADHPPolicy)
        assert p.level == "standard"

    def test_load_policy_from_policy(self):
        original = ADHPPolicy(level="strict", training_opt_out=True, third_party_opt_out=True, content_logging_opt_out=True)
        result = load_policy(original)
        assert result is original

    def test_load_policy_from_json_file(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"level": "sensitive", "compliance": ["GDPR"]}))
        p = load_policy(str(f))
        assert p.level == "sensitive"

    def test_load_policy_missing_file_raises(self):
        with pytest.raises(ADHPConfigError, match="not found"):
            load_policy("/nonexistent/path.json")

    def test_load_policy_invalid_json_raises(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json")
        with pytest.raises(ADHPConfigError, match="Invalid JSON"):
            load_policy(str(f))

    def test_load_requirements_from_dict(self):
        r = load_requirements({"min_level": "strict"})
        assert isinstance(r, ADHPClientRequirements)
        assert r.min_level == "strict"

    def test_load_requirements_from_file(self, tmp_path):
        f = tmp_path / "req.json"
        f.write_text(json.dumps({"min_level": "sensitive", "require_compliance": ["GDPR"]}))
        r = load_requirements(str(f))
        assert r.min_level == "sensitive"
        assert r.require_compliance == ["GDPR"]

    def test_load_from_env(self, monkeypatch):
        monkeypatch.setenv("ADHP_LEVEL", "strict")
        monkeypatch.setenv("ADHP_TRAINING_OPT_OUT", "true")
        monkeypatch.setenv("ADHP_COMPLIANCE", "GDPR,HIPAA")
        monkeypatch.setenv("ADHP_PROCESSING_JURISDICTION", "DE")
        p = load_policy("env")
        assert p.level == "strict"
        assert p.training_opt_out is True
        assert p.compliance == ["GDPR", "HIPAA"]
        assert p.processing_jurisdiction == ["DE"]


# ── Schema validation ─────────────────────────────────────────────────


class TestSchemaValidation:
    def test_valid_policy(self):
        # Note: the JSON Schema if/then for max_retention fires when property
        # is absent (JSON Schema quirk), so we must include retention_days and
        # session_ttl to satisfy both conditional branches, or set max_retention
        # explicitly to a non-custom/session value.
        errors = validate_policy_dict({"level": "standard", "max_retention": "7d"})
        assert errors == []

    def test_missing_level(self):
        errors = validate_policy_dict({})
        assert any("level" in e.lower() for e in errors)

    def test_invalid_level_value(self):
        errors = validate_policy_dict({"level": "invalid"})
        assert len(errors) > 0

    def test_valid_file(self, tmp_path):
        f = tmp_path / "valid.json"
        f.write_text(json.dumps({
            "level": "strict",
            "training_opt_out": True,
            "third_party_opt_out": True,
            "content_logging_opt_out": True,
            "max_retention": "request",
        }))
        errors = validate_policy_file(str(f))
        assert errors == []

    def test_invalid_file(self, tmp_path):
        f = tmp_path / "invalid.json"
        f.write_text(json.dumps({"level": "invalid_level"}))
        errors = validate_policy_file(str(f))
        assert len(errors) > 0

    def test_nonexistent_file(self):
        errors = validate_policy_file("/nonexistent.json")
        assert any("not found" in e.lower() for e in errors)

    def test_full_valid_policy(self):
        errors = validate_policy_dict({
            "level": "strict",
            "training_opt_out": True,
            "third_party_opt_out": True,
            "content_logging_opt_out": True,
            "max_retention": "request",
            "delegation_policy": "same_or_higher",
            "compliance": ["GDPR", "HIPAA"],
            "pii_categories": ["email", "health"],
            "processing_jurisdiction": ["DE"],
            "storage_jurisdiction": ["DE"],
            "execution_environment": "TEE",
        })
        assert errors == []
