from datetime import UTC, datetime
from typing import Any


ALLOWED_TRANSITIONS = {
    "open": {"in_progress", "resolved", "risk_accepted"},
    "in_progress": {"open", "resolved", "risk_accepted"},
    "resolved": {"open"},
    "risk_accepted": {"open"},
}


def validate_transition(result: Any, new_status: str, note: str | None) -> None:
    if result.compliant:
        raise ValueError("Compliant results do not require remediation.")
    current = result.remediation_status
    if new_status != current and new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Cannot move remediation from {current} to {new_status}.")
    if new_status == "risk_accepted" and not (note and note.strip()):
        raise ValueError("Risk acceptance requires a written justification.")


def resolution_time(new_status: str) -> datetime | None:
    return datetime.now(UTC) if new_status in {"resolved", "risk_accepted"} else None
