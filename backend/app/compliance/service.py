from collections import defaultdict
from typing import Any

from backend.app import schemas


DISCLAIMER = (
    "Readiness is an evidence-based CloudConform assessment, not an audit, "
    "certification, or endorsement by a framework publisher."
)

FIELD_CONTROL_CODES = {
    "public_access_blocked": {"CIS 3.3", "PR.AA-05", "A.5.15", "CC6.1"},
    "encryption_enabled": {"CIS 3.11", "PR.DS-01", "A.8.24", "CC6.7"},
}


def map_policy_to_controls(db: Any, policy: Any) -> None:
    """Attach a new supported policy to the product-authored crosswalk."""
    codes = FIELD_CONTROL_CODES.get(policy.rule_config.get("field"), set())
    if not codes:
        return
    from backend.app import models
    controls = db.query(models.FrameworkControl).filter(models.FrameworkControl.code.in_(codes)).all()
    for control in controls:
        db.add(models.PolicyFrameworkMapping(
            policy_id=policy.id, control_id=control.id,
            rationale=f"Policy evidence tests {policy.rule_config['field']}.",
        ))


def build_readiness(frameworks: list[Any], results: list[Any]) -> schemas.ComplianceReadinessResponse:
    """Calculate readiness from the newest stored result for each mapped policy."""
    latest_by_policy: dict[int, Any] = {}
    for result in sorted(results, key=lambda item: item.created_at, reverse=True):
        latest_by_policy.setdefault(result.policy_id, result)

    output: list[schemas.FrameworkReadiness] = []
    for framework in frameworks:
        controls: list[schemas.ControlReadiness] = []
        counts = defaultdict(int)
        for control in framework.controls:
            policy_ids = {mapping.policy_id for mapping in control.policy_mappings}
            evidence = [latest_by_policy[policy_id] for policy_id in policy_ids if policy_id in latest_by_policy]
            if not evidence:
                status = "not_assessed"
            elif any(not item.compliant and item.remediation_status in {"open", "in_progress", "resolved"} for item in evidence):
                status = "failed"
            elif any(not item.compliant and item.remediation_status == "risk_accepted" for item in evidence):
                status = "accepted"
            else:
                status = "passed"
            counts[status] += 1
            controls.append(schemas.ControlReadiness(
                code=control.code, title=control.title, domain=control.domain, status=status,
                mapped_policies=len(policy_ids), evidence_count=len(evidence),
            ))
        total = len(controls)
        readiness = round(counts["passed"] / total * 100) if total else 0
        output.append(schemas.FrameworkReadiness(
            slug=framework.slug, name=framework.name, version=framework.version,
            description=framework.description, source_url=framework.source_url,
            readiness_percent=readiness, passed=counts["passed"], failed=counts["failed"],
            accepted=counts["accepted"], not_assessed=counts["not_assessed"], controls=controls,
        ))
    return schemas.ComplianceReadinessResponse(disclaimer=DISCLAIMER, frameworks=output)
