from types import SimpleNamespace

import pytest

from backend.app import schemas
from backend.app.policies.engine import evaluate_matching_policies, evaluate_policy


def policy(**overrides):
    values = {
        "id": 1,
        "name": "Storage encryption enabled",
        "severity": "high",
        "cloud_provider": "aws",
        "resource_type": "storage_bucket",
        "rule_type": "boolean_property_equals",
        "rule_config": {"field": "encrypted", "expected_value": True},
        "is_active": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("configuration", "compliant"),
    [
        ({"encrypted": True}, True),
        ({"encrypted": False}, False),
        ({}, False),
    ],
)
def test_boolean_property_equals(configuration, compliant):
    result = evaluate_policy(policy(), configuration)

    assert result.compliant is compliant
    assert result.policy_id == 1
    assert "encrypted" in result.details


@pytest.mark.parametrize(
    ("value", "compliant"),
    [("owner@example.com", True), (None, False), ("", False), ([], False), ({}, False)],
)
def test_field_must_exist_rejects_empty_values(value, compliant):
    configured_policy = policy(
        rule_type="field_must_exist",
        rule_config={"field": "owner"},
    )

    result = evaluate_policy(configured_policy, {"owner": value})

    assert result.compliant is compliant


def test_matching_policies_only_evaluates_active_resource_matches():
    request = schemas.PolicyEvaluationRequest(
        resource_name="customer-data",
        cloud_provider="aws",
        resource_type="storage_bucket",
        configuration={"encrypted": True},
    )
    policies = [
        policy(id=1),
        policy(id=2, is_active=False),
        policy(id=3, cloud_provider="azure"),
        policy(id=4, resource_type="virtual_machine"),
    ]

    results = evaluate_matching_policies(policies, request)

    assert [result.policy_id for result in results] == [1]
    assert results[0].compliant is True


def test_unsupported_rule_type_fails_closed():
    result = evaluate_policy(policy(rule_type="unknown_rule"), {})

    assert result.compliant is False
    assert result.details == "Unsupported rule type: unknown_rule."
