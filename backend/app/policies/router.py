from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db
from backend.app.policies.engine import evaluate_matching_policies


router = APIRouter(prefix="/policies", tags=["Policies"])


def get_policy_or_404(policy_id: int, db: Session) -> models.Policy:
    """Return a policy or a clear not-found response."""
    policy = db.query(models.Policy).filter(
        models.Policy.id == policy_id
    ).first()
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found.",
        )
    return policy


@router.post("", response_model=schemas.Policy, status_code=status.HTTP_201_CREATED)
def create_policy(
    policy_data: schemas.PolicyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Policy:
    """Create an active security policy for later resource checks."""
    _ = current_user

    policy = models.Policy(**policy_data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


@router.get("", response_model=list[schemas.Policy])
def list_policies(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Policy]:
    """List active policies, with an option to include deactivated policies."""
    _ = current_user

    query = db.query(models.Policy)
    if not include_inactive:
        query = query.filter(models.Policy.is_active.is_(True))

    return query.order_by(models.Policy.created_at.desc()).all()


@router.post("/evaluate", response_model=schemas.PolicyEvaluationResponse)
def evaluate_resource_configuration(
    evaluation_request: schemas.PolicyEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.PolicyEvaluationResponse:
    """Evaluate matching active policies against a resource configuration."""
    _ = current_user

    policies = db.query(models.Policy).filter(
        models.Policy.is_active.is_(True),
        models.Policy.cloud_provider == evaluation_request.cloud_provider,
        models.Policy.resource_type == evaluation_request.resource_type,
    ).all()

    results = evaluate_matching_policies(policies, evaluation_request)

    return schemas.PolicyEvaluationResponse(
        resource_name=evaluation_request.resource_name,
        checked_policy_count=len(results),
        results=results,
    )


@router.get("/{policy_id}", response_model=schemas.Policy)
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Policy:
    """Return one policy by its ID."""
    _ = current_user
    return get_policy_or_404(policy_id, db)


@router.put("/{policy_id}", response_model=schemas.Policy)
def update_policy(
    policy_id: int,
    policy_data: schemas.PolicyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Policy:
    """Replace the editable settings of an existing policy."""
    _ = current_user
    policy = get_policy_or_404(policy_id, db)

    for field_name, value in policy_data.model_dump().items():
        setattr(policy, field_name, value)

    db.commit()
    db.refresh(policy)

    return policy


@router.delete("/{policy_id}", response_model=schemas.Policy)
def deactivate_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Policy:
    """Deactivate a policy without losing its historical record."""
    _ = current_user
    policy = get_policy_or_404(policy_id, db)

    policy.is_active = False
    db.commit()
    db.refresh(policy)

    return policy