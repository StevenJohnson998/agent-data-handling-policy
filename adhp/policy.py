"""ADHPPolicy convenience interface — wraps models and config loading."""

from __future__ import annotations

from pathlib import Path

from .config import load_policy
from .models import ADHPPolicy


def from_file(path: str | Path) -> ADHPPolicy:
    """Load an ADHPPolicy from a JSON or YAML file."""
    return load_policy(path)


def from_dict(data: dict) -> ADHPPolicy:
    """Create an ADHPPolicy from a dictionary."""
    return load_policy(data)


def from_env() -> ADHPPolicy:
    """Load an ADHPPolicy from ADHP_* environment variables."""
    return load_policy("env")
