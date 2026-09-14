import json
from typing import Any

from backend.app import schemas
from backend.app.intelligence.service import build_intelligence_graph
from config import settings


SYSTEM_PROMPT = """You are the CloudConform Security Agent.
You help a security operator understand stored CloudConform evidence.

Rules:
1. Use the supplied read-only tools before answering.
2. Treat deterministic policy results as the source of truth.
3. Never claim an audit, certification, or framework endorsement.
4. Never invent resources, findings, owners, or scan results.
5. Recommend actions but never mutate cloud infrastructure or CloudConform data.
6. State clearly when the available evidence cannot answer the question.
7. Give a concise answer with: assessment, evidence, recommended next action.
"""


def _snapshot(results: list[Any]) -> tuple[schemas.IntelligenceGraph, dict[str, Any]]:
    graph = build_intelligence_graph(results)
    evidence = {
        "summary": graph.summary.model_dump(),
        "priority_actions": [item.model_dump() for item in graph.priority_actions],
        "nodes": [item.model_dump() for item in graph.nodes],
    }
    return graph, evidence


def _preview_answer(graph: schemas.IntelligenceGraph) -> str:
    summary = graph.summary
    if not graph.priority_actions:
        return (
            "Assessment: no open findings appear in the stored scan evidence.\n\n"
            f"Evidence: {summary.resources} resources, {summary.policies} controls, "
            f"and {summary.scans} scans produce a risk score of {summary.risk_score}/100.\n\n"
            "Next action: continue scheduled verification scans and investigate any new "
            "finding before changing the compliance-readiness position."
        )
    action = graph.priority_actions[0]
    return (
        f"Assessment: the highest-priority open issue is {action.title} "
        f"({action.severity} severity).\n\n"
        f"Evidence: {summary.open_findings} open finding(s) produce a risk score of "
        f"{summary.risk_score}/100 across {summary.resources} connected resource(s).\n\n"
        f"Next action: {action.recommendation} Keep the finding open until a new scan "
        "provides verified passing evidence."
    )


def _result_text(result: Any) -> str:
    message = getattr(result, "message", None)
    if isinstance(message, dict):
        blocks = message.get("content", [])
        text = "\n".join(
            block["text"] for block in blocks
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        )
        if text:
            return text
    return str(result)


def _invoke_strands(question: str, evidence: dict[str, Any]) -> str:
    from strands import Agent, tool
    from strands.models import BedrockModel

    @tool
    def inspect_security_posture() -> str:
        """Return counts and the deterministic CloudConform risk score."""
        return json.dumps(evidence["summary"])

    @tool
    def inspect_priority_findings() -> str:
        """Return open findings ordered by deterministic policy severity."""
        return json.dumps(evidence["priority_actions"])

    @tool
    def trace_security_evidence() -> str:
        """Return stored resource, policy, scan, and finding evidence nodes."""
        return json.dumps(evidence["nodes"])

    model = BedrockModel(
        model_id=settings.BEDROCK_MODEL_ID,
        temperature=0.1,
        max_tokens=900,
    )
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            inspect_security_posture,
            inspect_priority_findings,
            trace_security_evidence,
        ],
    )
    return _result_text(agent(question))


def analyze_security(
    question: str,
    results: list[Any],
    *,
    force_preview: bool = False,
) -> schemas.SecurityAgentResponse:
    """Answer from persisted evidence without granting the model write access."""
    graph, evidence = _snapshot(results)
    use_strands = settings.SECURITY_AGENT_MODE == "strands" and not force_preview
    answer = _invoke_strands(question, evidence) if use_strands else _preview_answer(graph)
    return schemas.SecurityAgentResponse(
        answer=answer,
        mode="strands_bedrock" if use_strands else "evidence_preview",
        evidence=schemas.SecurityAgentEvidence(**graph.summary.model_dump()),
        tools_used=[
            "inspect_security_posture",
            "inspect_priority_findings",
            "trace_security_evidence",
        ],
        disclaimer=(
            "Advisory analysis based on stored CloudConform evidence; not an audit, "
            "certification, or autonomous remediation."
        ),
    )
