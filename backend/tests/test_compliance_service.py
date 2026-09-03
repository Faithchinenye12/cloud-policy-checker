from datetime import datetime
from types import SimpleNamespace

from backend.app.compliance.service import build_readiness


def item(**values):
    return SimpleNamespace(**values)


def result(policy_id, compliant, remediation_status):
    policy = item(name="Storage policy", severity="high", rule_type="boolean_property_equals", rule_config={"field":"encryption_enabled","expected_value":True})
    return item(id=policy_id, policy_id=policy_id, compliant=compliant, remediation_status=remediation_status, created_at=datetime(2026, 1, 2), policy=policy, resource=item(name="Bucket"))


def test_readiness_uses_latest_evidence_and_preserves_accepted_risk():
    mappings = [item(policy_id=1), item(policy_id=2)]
    control = item(code="TEST-1", title="Test", domain="Security", policy_mappings=mappings)
    framework = item(slug="test", name="Test Framework", version="1", description="Test", source_url="https://example.com", controls=[control])
    results = [
        result(1, True, "open"),
        result(2, False, "risk_accepted"),
    ]
    readiness = build_readiness([framework], results).frameworks[0]
    assert readiness.accepted == 1
    assert readiness.readiness_percent == 0


def test_resolved_failure_requires_verification_scan():
    control = item(code="TEST-2", title="Test", domain="Security", policy_mappings=[item(policy_id=1)])
    framework = item(slug="test", name="Test", version="1", description="Test", source_url="https://example.com", controls=[control])
    readiness = build_readiness([framework], [result(1, False, "resolved")]).frameworks[0]
    assert readiness.failed == 1
