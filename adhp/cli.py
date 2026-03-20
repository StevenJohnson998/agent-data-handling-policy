"""ADHP CLI — check, validate, init, inspect commands."""

from __future__ import annotations

import json
import sys

import click

from .checker import check_compliance
from .config import load_policy, load_requirements
from .exceptions import ADHPComplianceError, ADHPConfigError, ADHPConnectionError
from .models import ADHPClientRequirements, ADHPPolicy, LEVEL_ORDER
from .schema import validate_policy_file


@click.group()
@click.version_option(version="0.2.0", prog_name="adhp")
def cli():
    """ADHP SDK — Agent Data Handling Policy compliance tools."""
    pass


@cli.command()
@click.argument("url")
@click.option("--min-level", default="open", type=click.Choice(list(LEVEL_ORDER.keys())), help="Minimum ADHP level required")
@click.option("--require-compliance", "-c", multiple=True, help="Required compliance frameworks (repeat for multiple)")
@click.option("--require-jurisdiction", "-j", multiple=True, help="Accepted jurisdictions (repeat for multiple)")
@click.option("--require-training-opt-out", is_flag=True, help="Require training opt-out")
@click.option("--require-no-third-party", is_flag=True, help="Require no third-party sharing")
@click.option("--max-retention", type=click.Choice(["none", "request", "session", "24h", "7d", "30d", "custom", "unlimited"]), help="Maximum acceptable retention")
@click.option("--requirements-file", "-r", type=click.Path(exists=True), help="Load requirements from a JSON/YAML file")
def check(url, min_level, require_compliance, require_jurisdiction, require_training_opt_out, require_no_third_party, max_retention, requirements_file):
    """Check an MCP server's ADHP compliance."""
    from .client import ADHPClient

    if requirements_file:
        client = ADHPClient(requirements=requirements_file)
    else:
        client = ADHPClient(
            min_level=min_level,
            require_compliance=list(require_compliance),
            accepted_jurisdictions=list(require_jurisdiction),
            require_training_opt_out=require_training_opt_out,
            require_no_third_party=require_no_third_party,
            max_retention=max_retention,
        )

    try:
        result = client.check(url)
    except ADHPConnectionError as e:
        click.echo(f"\n  Connection error: {e}", err=True)
        sys.exit(1)

    _print_result(result)
    sys.exit(0 if result.compliant else 1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def validate(path):
    """Validate an ADHP config file against the JSON Schema."""
    errors = validate_policy_file(path)
    if not errors:
        click.echo(f"  Valid ADHP config: {path}")
    else:
        click.echo(f"  Invalid ADHP config: {path}", err=True)
        for err in errors:
            click.echo(f"    {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--level", default="standard", type=click.Choice(list(LEVEL_ORDER.keys())), help="ADHP level")
@click.option("--compliance", "-c", multiple=True, help="Compliance frameworks")
@click.option("--jurisdiction", "-j", multiple=True, help="Processing jurisdictions")
@click.option("--training-opt-out/--no-training-opt-out", default=False, help="Training opt-out flag")
@click.option("--third-party-opt-out/--no-third-party-opt-out", default=False, help="Third-party opt-out flag")
@click.option("--max-retention", default="session", type=click.Choice(["none", "request", "session", "24h", "7d", "30d", "custom", "unlimited"]), help="Max retention")
def init(level, compliance, jurisdiction, training_opt_out, third_party_opt_out, max_retention):
    """Generate a starter ADHP config (outputs JSON to stdout)."""
    config = {
        "level": level,
        "training_opt_out": training_opt_out,
        "third_party_opt_out": third_party_opt_out,
        "max_retention": max_retention,
        "delegation_policy": "none" if level == "zero-trace" else "same_or_higher",
        "compliance": list(compliance),
        "pii_categories": [],
        "processing_jurisdiction": list(jurisdiction),
        "storage_jurisdiction": list(jurisdiction),
        "log_jurisdiction": list(jurisdiction),
        "execution_environment": "standard",
    }

    # Apply level constraints
    if level in ("strict", "zero-trace"):
        config["training_opt_out"] = True
        config["third_party_opt_out"] = True
        config["content_logging_opt_out"] = True
    if level == "zero-trace":
        config["max_retention"] = "none"
        config["delegation_policy"] = "none"

    # Add conditional fields required by the JSON Schema
    if config["max_retention"] == "session":
        config["session_ttl"] = "4h"
    elif config["max_retention"] == "custom":
        config["retention_days"] = 30

    click.echo(json.dumps(config, indent=2))


@cli.command()
@click.argument("url")
def inspect(url):
    """Show what an MCP server declares for ADHP (pretty print)."""
    from .client import ADHPClient

    client = ADHPClient()  # No requirements — just fetching

    try:
        adhp_data = client._fetch_adhp(url)
    except ADHPConnectionError as e:
        click.echo(f"\n  Connection error: {e}", err=True)
        sys.exit(1)

    if adhp_data is None:
        click.echo("\n  No ADHP declaration found on this server.")
        sys.exit(1)

    click.echo(f"\n  ADHP Declaration from {url}")
    click.echo("  " + "=" * 50)
    click.echo(json.dumps(adhp_data, indent=2))


@cli.command(name="check-local")
@click.argument("policy_file", type=click.Path(exists=True))
@click.option("--requirements-file", "-r", type=click.Path(exists=True), help="Requirements JSON/YAML file")
@click.option("--min-level", default="open", type=click.Choice(list(LEVEL_ORDER.keys())))
@click.option("--require-compliance", "-c", multiple=True)
@click.option("--require-jurisdiction", "-j", multiple=True)
@click.option("--require-training-opt-out", is_flag=True)
@click.option("--require-no-third-party", is_flag=True)
@click.option("--max-retention", type=click.Choice(["none", "request", "session", "24h", "7d", "30d", "custom", "unlimited"]))
def check_local(policy_file, requirements_file, min_level, require_compliance, require_jurisdiction, require_training_opt_out, require_no_third_party, max_retention):
    """Check a local ADHP config file against requirements (no server needed)."""
    try:
        policy = load_policy(policy_file)
    except ADHPConfigError as e:
        click.echo(f"\n  Error loading policy: {e}", err=True)
        sys.exit(1)

    if requirements_file:
        requirements = load_requirements(requirements_file)
    else:
        requirements = ADHPClientRequirements(
            min_level=min_level,  # type: ignore[arg-type]
            require_compliance=list(require_compliance),
            accepted_jurisdictions=list(require_jurisdiction),
            require_training_opt_out=require_training_opt_out,
            require_no_third_party=require_no_third_party,
            max_retention=max_retention,  # type: ignore[arg-type]
        )

    result = check_compliance(requirements, policy)
    _print_result(result)
    sys.exit(0 if result.compliant else 1)


def _print_result(result):
    """Pretty-print a ComplianceResult."""
    if result.compliant:
        click.echo("\n  PASS — Server meets all ADHP requirements\n")
    else:
        click.echo("\n  FAIL — Server does NOT meet ADHP requirements\n")

    for c in result.checks:
        icon = "PASS" if c.passed else "FAIL"
        click.echo(f"    [{icon}] {c.name}: {c.reason}")

    click.echo()


def main():
    cli()


if __name__ == "__main__":
    main()
