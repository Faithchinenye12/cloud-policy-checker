from types import SimpleNamespace

import pytest

from backend.app.remediations.service import resolution_time, validate_transition


def finding(status="open", compliant=False):
    return SimpleNamespace(remediation_status=status, compliant=compliant)


def test_open_finding_can_move_to_in_progress():
    validate_transition(finding(), "in_progress", None)


def test_risk_acceptance_requires_justification():
    with pytest.raises(ValueError, match="written justification"):
        validate_transition(finding(), "risk_accepted", "  ")


def test_closed_finding_must_reopen_before_another_terminal_state():
    with pytest.raises(ValueError, match="Cannot move"):
        validate_transition(finding("resolved"), "risk_accepted", "Approved")


def test_compliant_result_cannot_enter_workflow():
    with pytest.raises(ValueError, match="do not require"):
        validate_transition(finding(compliant=True), "in_progress", None)


def test_terminal_status_has_resolution_timestamp():
    assert resolution_time("resolved") is not None
    assert resolution_time("risk_accepted") is not None
    assert resolution_time("open") is None
