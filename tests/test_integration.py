"""Integration tests — start server, connect client, verify."""

import json
import multiprocessing
import time

import pytest
import httpx

from adhp import ADHPClient, ADHPPolicy, ADHPServer, check_compliance
from adhp.models import ADHPClientRequirements


# ── Helpers ───────────────────────────────────────────────────────────

def _run_server(config_dict: dict, port: int):
    """Run an ADHPServer in a subprocess."""
    policy = ADHPPolicy(**config_dict)
    server = ADHPServer(name="Test Server", version="0.1.0", policy=policy)
    server.run(host="127.0.0.1", port=port)


def _start_server(config_dict: dict, port: int) -> multiprocessing.Process:
    """Start a server process and wait for it to be ready."""
    proc = multiprocessing.Process(target=_run_server, args=(config_dict, port), daemon=True)
    proc.start()
    # Wait for server to be ready
    for _ in range(30):
        try:
            resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1)
            if resp.status_code == 200:
                return proc
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(0.2)
    proc.kill()
    raise RuntimeError(f"Server on port {port} did not start in time")


# ── Test configs ──────────────────────────────────────────────────────

STRICT_DE_CONFIG = {
    "level": "strict",
    "training_opt_out": True,
    "third_party_opt_out": True,
    "content_logging_opt_out": True,
    "max_retention": "request",
    "delegation_policy": "same_or_higher",
    "compliance": ["GDPR", "HIPAA"],
    "processing_jurisdiction": ["DE"],
    "storage_jurisdiction": ["DE"],
    "log_jurisdiction": ["DE"],
}

OPEN_CONFIG = {
    "level": "open",
}


# ── Integration tests ────────────────────────────────────────────────


class TestServerClientIntegration:
    """Test real HTTP connections between ADHPServer and ADHPClient."""

    @pytest.fixture(autouse=True)
    def _setup_servers(self):
        """Start test servers before each test class and stop after."""
        self.strict_proc = _start_server(STRICT_DE_CONFIG, 9150)
        self.open_proc = _start_server(OPEN_CONFIG, 9151)
        yield
        self.strict_proc.kill()
        self.open_proc.kill()
        self.strict_proc.join(timeout=2)
        self.open_proc.join(timeout=2)

    def test_client_gets_adhp_from_server(self):
        """Scenario 1: Client connects → gets ADHP in capabilities."""
        client = ADHPClient()
        adhp_data = client._fetch_adhp("http://127.0.0.1:9150/mcp")
        assert adhp_data is not None
        assert adhp_data["level"] == "strict"
        assert "GDPR" in adhp_data["compliance"]

    def test_compliant_server_passes(self):
        """Scenario 2: Client with strict requirements → compliant server → PASS."""
        client = ADHPClient(
            min_level="strict",
            require_compliance=["GDPR", "HIPAA"],
            accepted_jurisdictions=["DE"],
            require_training_opt_out=True,
            require_no_third_party=True,
        )
        result = client.check("http://127.0.0.1:9150/mcp")
        assert result.compliant

    def test_non_compliant_server_fails(self):
        """Scenario 3: Client with strict requirements → non-compliant server → FAIL."""
        client = ADHPClient(
            min_level="strict",
            require_compliance=["GDPR"],
        )
        result = client.check("http://127.0.0.1:9151/mcp")
        assert not result.compliant

    def test_health_endpoint(self):
        """Server health endpoint works."""
        resp = httpx.get("http://127.0.0.1:9150/health", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["adhp_level"] == "strict"

    def test_adhp_endpoint(self):
        """Direct /adhp endpoint returns policy."""
        resp = httpx.get("http://127.0.0.1:9150/adhp", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == "strict"

    def test_open_server_no_requirements_passes(self):
        """Open server with no client requirements passes."""
        client = ADHPClient()
        result = client.check("http://127.0.0.1:9151/mcp")
        assert result.compliant


class TestCLIIntegration:
    """Test CLI commands (using Click's test runner)."""

    def test_validate_valid_config(self, tmp_path):
        """Scenario 5: CLI validate on valid config → success."""
        from click.testing import CliRunner
        from adhp.cli import cli

        f = tmp_path / "valid.json"
        f.write_text(json.dumps({"level": "standard", "max_retention": "7d"}))

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(f)])
        assert result.exit_code == 0
        assert "Valid" in result.output

    def test_validate_invalid_config(self, tmp_path):
        """Scenario 6: CLI validate on invalid config → error."""
        from click.testing import CliRunner
        from adhp.cli import cli

        f = tmp_path / "invalid.json"
        f.write_text(json.dumps({"level": "not_a_level"}))

        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(f)])
        assert result.exit_code != 0

    def test_init_generates_valid_config(self):
        """Scenario 7: CLI init generates valid config."""
        from click.testing import CliRunner
        from adhp.cli import cli
        from adhp.schema import validate_policy_dict

        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--level", "standard", "-c", "GDPR", "-j", "DE"])
        assert result.exit_code == 0
        config = json.loads(result.output)
        assert config["level"] == "standard"
        assert "GDPR" in config["compliance"]
        # Validate against schema
        errors = validate_policy_dict(config)
        assert errors == []

    def test_check_local_compliant(self, tmp_path):
        """CLI check-local on compliant config."""
        from click.testing import CliRunner
        from adhp.cli import cli

        f = tmp_path / "policy.json"
        f.write_text(json.dumps({
            "level": "strict",
            "training_opt_out": True,
            "third_party_opt_out": True,
            "content_logging_opt_out": True,
            "compliance": ["GDPR"],
            "processing_jurisdiction": ["DE"],
            "storage_jurisdiction": ["DE"],
            "log_jurisdiction": ["DE"],
        }))

        runner = CliRunner()
        result = runner.invoke(cli, [
            "check-local", str(f),
            "--min-level", "standard",
            "-c", "GDPR",
            "-j", "DE",
        ])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_check_local_non_compliant(self, tmp_path):
        """CLI check-local on non-compliant config."""
        from click.testing import CliRunner
        from adhp.cli import cli

        f = tmp_path / "policy.json"
        f.write_text(json.dumps({"level": "open"}))

        runner = CliRunner()
        result = runner.invoke(cli, [
            "check-local", str(f),
            "--min-level", "strict",
        ])
        assert result.exit_code != 0
        assert "FAIL" in result.output
