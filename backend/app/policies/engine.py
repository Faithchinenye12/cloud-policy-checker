from typing import Any

from backend.app import models, schemas


def evaluate_policy(
    policy: models.Policy,
    configuration: dict[str, Any],
) -> schemas.PolicyEvaluationResult:
    """Evaluate one policy against a resource configuration."""
    field_name = policy.rule_config["field"]

    if policy.rule_type == "boolean_property_equals":
        expected_value = policy.rule_config["expected_value"]
        actual_value = configuration.get(field_name)
        compliant = actual_value is expected_value

        if compliant:
            details = (
                f"{field_name} is set to {actual_value}, which matches the "
                f"required value {expected_value}."
            )
        elif field_name not in configuration:
            details = (
                f"{field_name} is missing. This policy requires the value "
                f"{expected_value}."
            )
        else:
            details = (
                f"{field_name} is set to {actual_value}, but this policy "
                f"requires {expected_value}."
            )

    elif policy.rule_type == "field_must_exist":
        value_exists = field_name in configuration and configuration[field_name] not in (
            None,
            "",
            [],
            {},
        )
        compliant = value_exists

        if compliant:
            details = f"Required field {field_name} is present in the configuration."
        else:
            details = f"Required field {field_name} is missing or empty."

    else:
        compliant = False
        details = f"Unsupported rule type: {policy.rule_type}."

    return schemas.PolicyEvaluationResult(
        policy_id=policy.id,
        policy_name=policy.name,
        severity=policy.severity,
        compliant=compliant,
        details=details,
    )


def evaluate_matching_policies(
    policies: list[models.Policy],
    request: schemas.PolicyEvaluationRequest,
) -> list[schemas.PolicyEvaluationResult]:
    """Evaluate every active policy that matches the resource being checked."""
    matching_policies = [
        policy
        for policy in policies
        if policy.is_active
        and policy.cloud_provider == request.cloud_provider
        and policy.resource_type == request.resource_type
    ]

    return [
        evaluate_policy(policy, request.configuration)
        for policy in matching_policies
    ]