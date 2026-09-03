from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db
from backend.app.remediations.service import resolution_time, validate_transition


router = APIRouter(prefix="/remediations", tags=["Remediations"])


def _query(db: Session):
    return db.query(models.ComplianceResult).options(
        joinedload(models.ComplianceResult.resource),
        joinedload(models.ComplianceResult.policy),
        joinedload(models.ComplianceResult.remediation_events),
    ).filter(models.ComplianceResult.compliant.is_(False))


@router.get("", response_model=list[schemas.RemediationRecord])
def list_remediations(
    remediation_status: Optional[schemas.RemediationStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.ComplianceResult]:
    _ = current_user
    query = _query(db)
    if remediation_status is not None:
        query = query.filter(models.ComplianceResult.remediation_status == remediation_status)
    return query.order_by(models.ComplianceResult.created_at.desc()).all()


@router.patch("/{result_id}", response_model=schemas.RemediationRecord)
def update_remediation(
    result_id: int,
    update: schemas.RemediationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.ComplianceResult:
    result = _query(db).filter(models.ComplianceResult.id == result_id).first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remediation finding not found.")
    if update.assigned_to_user_id is not None and db.get(models.User, update.assigned_to_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned user not found.")
    try:
        validate_transition(result, update.status, update.note)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    previous_status = result.remediation_status
    result.remediation_status = update.status
    result.assigned_to_user_id = update.assigned_to_user_id
    result.due_at = update.due_at
    result.remediation_note = update.note
    result.resolved_at = resolution_time(update.status)
    db.add(models.RemediationEvent(
        compliance_result_id=result.id,
        actor_user_id=current_user.id,
        previous_status=previous_status,
        new_status=update.status,
        note=update.note,
    ))
    db.commit()
    db.refresh(result)
    return result
