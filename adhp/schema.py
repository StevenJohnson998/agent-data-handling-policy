"""JSON Schema validation for ADHP policies."""

from __future__ import annotations

import json
from pathlib import Path

from .exceptions import ADHPValidationError

# Path to the bundled schema
_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
_SCHEMA_PATH = _SCHEMA_DIR / "adhp-v0.2.schema.json"


def _load_schema() -> dict:
    """Load the ADHP v0.2 JSON Schema."""
    if not _SCHEMA_PATH.exists():
        raise ADHPValidationError(f"Schema file not found: {_SCHEMA_PATH}")
    return json.loads(_SCHEMA_PATH.read_text())


def validate_policy_dict(data: dict) -> list[str]:
    """Validate a raw dict against the ADHP v0.2 JSON Schema.

    Returns a list of error messages (empty = valid).
    """
    try:
        import jsonschema
    except ImportError:
        raise ADHPValidationError(
            "jsonschema package required for schema validation. "
            "Install with: pip install adhp[schema] or pip install jsonschema"
        )

    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    return [_format_error(e) for e in errors]


def validate_policy_file(path: str | Path) -> list[str]:
    """Validate a JSON or YAML file against the ADHP v0.2 schema.

    Returns a list of error messages (empty = valid).
    """
    path = Path(path)
    if not path.exists():
        return [f"File not found: {path}"]

    text = path.read_text()

    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml

            data = yaml.safe_load(text)
        except ImportError:
            return ["PyYAML required to validate YAML files. Install with: pip install pyyaml"]
        except yaml.YAMLError as e:
            return [f"Invalid YAML: {e}"]
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return [f"Invalid JSON: {e}"]

    if not isinstance(data, dict):
        return ["Config must be a JSON object"]

    return validate_policy_dict(data)


def _format_error(error) -> str:
    """Format a jsonschema ValidationError into a readable string."""
    path = ".".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"
