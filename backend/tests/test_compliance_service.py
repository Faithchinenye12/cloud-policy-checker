from datetime import datetime
from types import SimpleNamespace

from backend.app.compliance.service import build_readiness


def item(**values):
    return SimpleNamespace(**values)


def test_readiness_uses_latest_evidence_and_preserves_accepted_risk():
    mappings = [item(policy_id=1), item(policy_id=2)]
    control = item(code="TEST-1", title="Test", domain="Security", policy_mappings=mappings)
    framework = item(slug="test", name="Test Framework", version="1", description="Test", source_url="https://example.com", controls=[control])
    results = [
        item(policy_id=1, compliant=True, remediation_status="open", created_at=datetime(2026, 1, 2)),
        item(policy_id=2, compliant=False, remediation_status="risk_accepted", created_at=datetime(2026, 1, 2)),
    ]
    readiness = build_readiness([framework], results).frameworks[0]
    assert readiness.accepted == 1
    assert readiness.readiness_percent == 0


def test_resolved_failure_requires_verification_scan():
    control = item(code="TEST-2", title="Test", domain="Security", policy_mappings=[item(policy_id=1)])
    framework = item(slug="test", name="Test", version="1", description="Test", source_url="https://example.com", controls=[control])
    result = item(policy_id=1, compliant=False, remediation_status="resolved", created_at=datetime(2026, 1, 1))
    readiness = build_readiness([framework], [result]).frameworks[0]
    assert readiness.failed == 1
