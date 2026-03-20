"""Load ADHP configuration from JSON, YAML, or environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .exceptions import ADHPConfigError
from .models import ADHPClientRequirements, ADHPPolicy


def load_policy(source: str | Path | dict | ADHPPolicy) -> ADHPPolicy:
    """Load an ADHPPolicy from various sources.

    Args:
        source: One of:
            - ADHPPolicy instance (returned as-is)
            - dict (parsed directly)
            - str/Path to a .json or .yaml/.yml file
            - str "env" to load from environment variables

    Returns:
        ADHPPolicy instance.
    """
    if isinstance(source, ADHPPolicy):
        return source

    if isinstance(source, dict):
        try:
            return ADHPPolicy(**source)
        except Exception as e:
            raise ADHPConfigError(f"Invalid policy dict: {e}") from e

    source_str = str(source)

    if source_str == "env":
        return _load_from_env()

    return _load_from_file(Path(source_str))


def load_requirements(source: str | Path | dict | ADHPClientRequirements) -> ADHPClientRequirements:
    """Load ADHPClientRequirements from various sources.

    Args:
        source: One of:
            - ADHPClientRequirements instance (returned as-is)
            - dict (parsed directly)
            - str/Path to a .json or .yaml/.yml file

    Returns:
        ADHPClientRequirements instance.
    """
    if isinstance(source, ADHPClientRequirements):
        return source

    if isinstance(source, dict):
        try:
            return ADHPClientRequirements(**source)
        except Exception as e:
            raise ADHPConfigError(f"Invalid requirements dict: {e}") from e

    return _load_requirements_from_file(Path(str(source)))


def _load_from_file(path: Path) -> ADHPPolicy:
    """Load policy from a JSON or YAML file."""
    if not path.exists():
        raise ADHPConfigError(f"Config file not found: {path}")

    text = path.read_text()
    data = _parse_file(path, text)

    try:
        return ADHPPolicy(**data)
    except Exception as e:
        raise ADHPConfigError(f"Invalid policy in {path}: {e}") from e


def _load_requirements_from_file(path: Path) -> ADHPClientRequirements:
    """Load requirements from a JSON or YAML file."""
    if not path.exists():
        raise ADHPConfigError(f"Config file not found: {path}")

    text = path.read_text()
    data = _parse_file(path, text)

    try:
        return ADHPClientRequirements(**data)
    except Exception as e:
        raise ADHPConfigError(f"Invalid requirements in {path}: {e}") from e


def _parse_file(path: Path, text: str) -> dict:
    """Parse JSON or YAML file content."""
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise ADHPConfigError("PyYAML required for YAML config files. Install: pip install pyyaml")
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise ADHPConfigError(f"Invalid YAML in {path}: {e}") from e
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ADHPConfigError(f"Invalid JSON in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ADHPConfigError(f"Config file must contain a JSON object, got {type(data).__name__}")

    return data


def _load_from_env() -> ADHPPolicy:
    """Load policy from environment variables (ADHP_ prefix)."""
    level = os.environ.get("ADHP_LEVEL")
    if not level:
        raise ADHPConfigError("ADHP_LEVEL environment variable is required")

    def _bool(key: str, default: bool = False) -> bool:
        val = os.environ.get(key, "").lower()
        if val in ("1", "true", "yes"):
            return True
        if val in ("0", "false", "no", ""):
            return default
        return default

    def _list(key: str) -> list[str]:
        val = os.environ.get(key, "").strip()
        if not val:
            return []
        return [v.strip() for v in val.split(",") if v.strip()]

    return ADHPPolicy(
        level=level,  # type: ignore[arg-type]
        training_opt_out=_bool("ADHP_TRAINING_OPT_OUT"),
        third_party_opt_out=_bool("ADHP_THIRD_PARTY_OPT_OUT"),
        content_logging_opt_out=_bool("ADHP_CONTENT_LOGGING_OPT_OUT"),
        output_sanitization_opt_in=_bool("ADHP_OUTPUT_SANITIZATION_OPT_IN"),
        max_retention=os.environ.get("ADHP_MAX_RETENTION", "unlimited"),  # type: ignore[arg-type]
        delegation_policy=os.environ.get("ADHP_DELEGATION_POLICY", "unrestricted"),  # type: ignore[arg-type]
        compliance=_list("ADHP_COMPLIANCE"),
        pii_categories=_list("ADHP_PII_CATEGORIES"),  # type: ignore[arg-type]
        processing_jurisdiction=_list("ADHP_PROCESSING_JURISDICTION"),
        storage_jurisdiction=_list("ADHP_STORAGE_JURISDICTION"),
        log_jurisdiction=_list("ADHP_LOG_JURISDICTION"),
    )
