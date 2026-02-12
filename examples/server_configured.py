"""Fully configured ADHP server with all fields."""

from adhp import ADHPPolicy, ADHPServer
from adhp.models import ThirdPartySharing

policy = ADHPPolicy(
    level="strict",
    training_opt_out=True,
    third_party_opt_out=True,
    content_logging_opt_out=True,
    output_sanitization_opt_in=True,
    max_retention="request",
    delegation_policy="same_or_higher",
    compliance=["GDPR", "HIPAA"],
    pii_categories=["health", "identity", "email", "financial"],
    processing_jurisdiction=["DE"],
    storage_jurisdiction=["DE"],
    log_jurisdiction=["DE"],
    execution_environment="TEE",
    third_party_sharing=ThirdPartySharing(enabled=False),
)

server = ADHPServer(
    name="HealthcareAnalyzer Pro",
    version="2.0.0",
    policy=policy,
)


@server.tool()
def analyze_patient(record_id: str) -> str:
    return f"Analysis complete for record {record_id}"


@server.tool()
def summarize_lab_results(patient_id: str) -> str:
    return f"Lab results summary for {patient_id}"


if __name__ == "__main__":
    server.run(port=8000)
