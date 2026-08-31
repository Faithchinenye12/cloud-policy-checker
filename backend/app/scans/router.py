from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db
from backend.app.policies.engine import evaluate_policy


router = APIRouter(prefix="/scans", tags=["Scans"])


def get_scan_or_404(
    scan_id: int,
    db: Session,
) -> models.Scan:
    """Return a scan or a clear not-found response."""
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id)
        .first()
    )

    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found.",
        )

    return scan


def validate_organization(
    organization_id: Optional[int],
    db: Session,
) -> None:
    """Confirm an optional organization ID exists."""
    if organization_id is None:
        return

    organization_exists = (
        db.query(models.Organization.id)
        .filter(models.Organization.id == organization_id)
        .first()
    )

    if organization_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )


@router.post(
    "",
    response_model=schemas.Scan,
    status_code=status.HTTP_201_CREATED,
)
def create_scan(
    scan_data: schemas.ScanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scan:
    """Create a pending local compliance scan request."""
    validate_organization(
        scan_data.organization_id,
        db,
    )

    scan = models.Scan(
        **scan_data.model_dump(),
        requested_by_user_id=current_user.id,
        status="pending",
    )

    db.add(scan)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The scan could not be created.",
        ) from exc

    db.refresh(scan)
    return scan


@router.get("", response_model=list[schemas.Scan])
def list_scans(
    scan_status: Optional[schemas.ScanStatus] = None,
    cloud_provider: Optional[schemas.CloudProvider] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Scan]:
    """List scan records with optional status and cloud filters."""
    _ = current_user
    query = db.query(models.Scan)

    if scan_status is not None:
        query = query.filter(models.Scan.status == scan_status)

    if cloud_provider is not None:
        query = query.filter(
            models.Scan.cloud_provider == cloud_provider
        )

    return query.order_by(models.Scan.created_at.desc()).all()


@router.get("/{scan_id}", response_model=schemas.Scan)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scan:
    """Return one scan and its current lifecycle status."""
    _ = current_user
    return get_scan_or_404(scan_id, db)


@router.post("/{scan_id}/run", response_model=schemas.Scan)
def run_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scan:
    """
    Run a deterministic local scan against stored resource configuration.

    This is intentionally synchronous for the Day 6 foundation. A future
    worker will move this processing into a Redis-backed background job.
    """
    _ = current_user
    scan = get_scan_or_404(scan_id, db)

    if scan.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This scan is already running.",
        )

    if scan.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This scan has already completed.",
        )

    scan.status = "running"
    scan.started_at = datetime.utcnow()
    scan.completed_at = None
    scan.error_message = None
    scan.total_resources = 0
    scan.compliant_count = 0
    scan.non_compliant_count = 0
    db.commit()

    try:
        resource_query = db.query(models.Resource).filter(
            models.Resource.status == "active",
            models.Resource.cloud_provider == scan.cloud_provider,
        )

        if scan.organization_id is not None:
            resource_query = resource_query.filter(
                models.Resource.organization_id == scan.organization_id
            )

        if scan.resource_type is not None:
            resource_query = resource_query.filter(
                models.Resource.resource_type == scan.resource_type
            )

        resources = resource_query.all()

        existing_results = db.query(models.ComplianceResult).filter(
            models.ComplianceResult.scan_id == scan.id
        )
        existing_results.delete(synchronize_session=False)

        compliant_resources = 0
        non_compliant_resources = 0

        for resource in resources:
            policies = db.query(models.Policy).filter(
                models.Policy.is_active.is_(True),
                models.Policy.cloud_provider == resource.cloud_provider,
                models.Policy.resource_type == resource.resource_type,
            ).all()

            evaluations = [
                evaluate_policy(policy, resource.configuration)
                for policy in policies
            ]

            for evaluation in evaluations:
                compliance_result = models.ComplianceResult(
                    scan_id=scan.id,
                    resource_id=resource.id,
                    policy_id=evaluation.policy_id,
                    compliant=evaluation.compliant,
                    details=evaluation.details,
                )
                db.add(compliance_result)

            if evaluations:
                if all(
                    evaluation.compliant
                    for evaluation in evaluations
                ):
                    compliant_resources += 1
                else:
                    non_compliant_resources += 1

        scan.total_resources = len(resources)
        scan.compliant_count = compliant_resources
        scan.non_compliant_count = non_compliant_resources
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(scan)

        return scan

    except Exception as exc:
        db.rollback()

        failed_scan = get_scan_or_404(scan_id, db)
        failed_scan.status = "failed"
        failed_scan.completed_at = datetime.utcnow()
        failed_scan.error_message = (
            "The local scan could not be completed."
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The local scan could not be completed.",
        ) from exc


@router.get(
    "/{scan_id}/results",
    response_model=list[schemas.ComplianceResult],
)
def list_scan_results(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.ComplianceResult]:
    """Return the stored policy results produced by one scan."""
    _ = current_user
    get_scan_or_404(scan_id, db)

    return (
        db.query(models.ComplianceResult)
        .filter(models.ComplianceResult.scan_id == scan_id)
        .order_by(models.ComplianceResult.created_at.asc())
        .all()
    )