from types import SimpleNamespace

from backend.app.intelligence.service import build_intelligence_graph


def evidence(result_id=1, compliant=False, severity="high"):
    resource = SimpleNamespace(
        id=10,
        name="Customer data bucket",
        status="active",
        cloud_provider="aws",
        resource_type="storage_bucket",
        region="eu-west-2",
    )
    policy = SimpleNamespace(
        id=20,
        name="Block public access",
        severity=severity,
        is_active=True,
        rule_type="boolean_property_equals",
        rule_config={"field": "public_access_blocked", "expected_value": True},
    )
    scan = SimpleNamespace(id=30, status="completed", cloud_provider="aws")
    return SimpleNamespace(
        id=result_id,
        compliant=compliant,
        details="Configuration does not match.",
        remediation_status="open",
        resource=resource,
        policy=policy,
        scan=scan,
    )


def test_graph_links_stored_evidence_and_prioritizes_remediation():
    graph = build_intelligence_graph([evidence()])

    assert graph.summary.resources == 1
    assert graph.summary.open_findings == 1
    assert graph.summary.risk_score == 25
    assert {node.kind for node in graph.nodes} == {
        "resource", "policy", "scan", "finding"
    }
    assert any(edge.relationship == "affects" for edge in graph.edges)
    assert graph.priority_actions[0].recommendation == (
        "Set public_access_blocked to True and run a verification scan."
    )


def test_graph_deduplicates_entities_and_caps_risk_score():
    graph = build_intelligence_graph(
        [evidence(result_id=index, severity="critical") for index in range(1, 5)]
    )

    assert graph.summary.resources == 1
    assert graph.summary.policies == 1
    assert graph.summary.scans == 1
    assert graph.summary.open_findings == 4
    assert graph.summary.risk_score == 100


def test_compliant_evidence_has_no_priority_action():
    graph = build_intelligence_graph([evidence(compliant=True)])

    assert graph.summary.open_findings == 0
    assert graph.summary.risk_score == 0
    assert graph.priority_actions == []


def test_resolved_evidence_remains_in_graph_without_active_risk():
    result = evidence()
    result.remediation_status = "resolved"
    graph = build_intelligence_graph([result])

    assert any(node.kind == "finding" for node in graph.nodes)
    assert graph.summary.open_findings == 0
    assert graph.summary.risk_score == 0
    assert graph.priority_actions == []
