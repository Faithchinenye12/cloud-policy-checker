from collections.abc import Iterable
from typing import Any

from backend.app import schemas


SEVERITY_WEIGHT = {"critical": 40, "high": 25, "medium": 12, "low": 5}


def _node_id(kind: str, record_id: int) -> str:
    return f"{kind}:{record_id}"


def _recommendation(policy: Any) -> str:
    field = policy.rule_config.get("field", "required setting")
    if policy.rule_type == "boolean_property_equals":
        expected = policy.rule_config.get("expected_value")
        return f"Set {field} to {expected} and run a verification scan."
    return f"Configure a non-empty value for {field} and run a verification scan."


def build_intelligence_graph(results: Iterable[Any]) -> schemas.IntelligenceGraph:
    """Project stored compliance evidence into a deterministic risk graph."""
    nodes: dict[str, schemas.IntelligenceNode] = {}
    edges: set[tuple[str, str, str]] = set()
    actions: list[schemas.IntelligenceAction] = []
    resource_ids: set[int] = set()
    policy_ids: set[int] = set()
    scan_ids: set[int] = set()
    risk_points = 0

    for result in results:
        resource, policy, scan = result.resource, result.policy, result.scan
        resource_id = _node_id("resource", resource.id)
        policy_id = _node_id("policy", policy.id)
        scan_id = _node_id("scan", scan.id)
        finding_id = _node_id("finding", result.id)
        severity = policy.severity.lower()
        result_status = "compliant" if result.compliant else "open"

        resource_ids.add(resource.id)
        policy_ids.add(policy.id)
        scan_ids.add(scan.id)
        nodes[resource_id] = schemas.IntelligenceNode(
            id=resource_id,
            kind="resource",
            label=resource.name,
            status=resource.status,
            metadata={
                "provider": resource.cloud_provider,
                "resource_type": resource.resource_type,
                "region": resource.region,
            },
        )
        nodes[policy_id] = schemas.IntelligenceNode(
            id=policy_id,
            kind="policy",
            label=policy.name,
            status="active" if policy.is_active else "inactive",
            severity=severity,
            metadata={"rule_type": policy.rule_type},
        )
        nodes[scan_id] = schemas.IntelligenceNode(
            id=scan_id,
            kind="scan",
            label=f"Scan #{scan.id}",
            status=scan.status,
            metadata={"provider": scan.cloud_provider},
        )
        nodes[finding_id] = schemas.IntelligenceNode(
            id=finding_id,
            kind="finding",
            label=policy.name,
            status=result_status,
            severity=severity,
            metadata={"details": result.details, "compliant": result.compliant},
        )
        edges.update(
            {
                (scan_id, resource_id, "evaluated"),
                (resource_id, policy_id, "checked_by"),
                (scan_id, finding_id, "produced"),
                (finding_id, resource_id, "affects"),
                (finding_id, policy_id, "violates"),
            }
        )

        remediation_status = getattr(result, "remediation_status", "open")
        if not result.compliant and remediation_status in {"open", "in_progress"}:
            risk_points += SEVERITY_WEIGHT.get(severity, 10)
            actions.append(
                schemas.IntelligenceAction(
                    finding_id=result.id,
                    resource_id=resource.id,
                    policy_id=policy.id,
                    severity=severity,
                    title=f"Remediate {resource.name}",
                    recommendation=_recommendation(policy),
                )
            )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    actions.sort(key=lambda item: (severity_order.get(item.severity, 4), item.finding_id))
    graph_edges = [
        schemas.IntelligenceEdge(source=source, target=target, relationship=relationship)
        for source, target, relationship in sorted(edges)
    ]
    return schemas.IntelligenceGraph(
        summary=schemas.IntelligenceSummary(
            resources=len(resource_ids),
            policies=len(policy_ids),
            scans=len(scan_ids),
            open_findings=len(actions),
            risk_score=min(risk_points, 100),
        ),
        nodes=list(nodes.values()),
        edges=graph_edges,
        priority_actions=actions,
    )
