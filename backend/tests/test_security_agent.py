from types import SimpleNamespace

from backend.app.security_agent import service


def evidence_result(*, compliant: bool = False):
    return SimpleNamespace(
        id=31,
        compliant=compliant,
        details="public_access_blocked is False; expected True",
        remediation_status="open",
        resource=SimpleNamespace(
            id=11,
            name="Customer Evidence Vault",
            status="active",
            cloud_provider="aws",
            resource_type="storage_bucket",
            region="eu-west-2",
        ),
        policy=SimpleNamespace(
            id=21,
            name="AWS storage buckets must block public access",
            severity="high",
            is_active=True,
            rule_type="boolean_property_equals",
            rule_config={"field": "public_access_blocked", "expected_value": True},
        ),
        scan=SimpleNamespace(id=41, status="completed", cloud_provider="aws"),
    )


def test_preview_agent_is_grounded_in_priority_evidence(monkeypatch):
    monkeypatch.setattr(service.settings, "SECURITY_AGENT_MODE", "preview")
    response = service.analyze_security(
        "What should we fix first?",
        [evidence_result()],
    )
    assert response.mode == "evidence_preview"
    assert response.evidence.risk_score == 25
    assert response.evidence.open_findings == 1
    assert "Customer Evidence Vault" in response.answer
    assert "public_access_blocked" in response.answer
    assert len(response.tools_used) == 3


def test_demo_session_can_be_forced_to_preview(monkeypatch):
    monkeypatch.setattr(service.settings, "SECURITY_AGENT_MODE", "strands")
    monkeypatch.setattr(
        service,
        "_invoke_strands",
        lambda *_: (_ for _ in ()).throw(AssertionError("Bedrock must not be called")),
    )
    response = service.analyze_security(
        "Summarise our posture",
        [evidence_result()],
        force_preview=True,
    )
    assert response.mode == "evidence_preview"


def test_strands_mode_returns_model_answer(monkeypatch):
    monkeypatch.setattr(service.settings, "SECURITY_AGENT_MODE", "strands")
    monkeypatch.setattr(
        service,
        "_invoke_strands",
        lambda question, evidence: f"Grounded answer for {evidence['summary']['risk_score']}",
    )
    response = service.analyze_security(
        "Summarise our posture",
        [evidence_result()],
    )
    assert response.mode == "strands_bedrock"
    assert response.answer == "Grounded answer for 25"
