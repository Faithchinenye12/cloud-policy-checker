from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db
from backend.app.tasks import run_scan_task


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
    """Create a pending compliance scan request."""
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
    """Return one scan and its background-processing status."""
    _ = current_user
    return get_scan_or_404(scan_id, db)


@router.post(
    "/{scan_id}/run",
    response_model=schemas.Scan,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scan:
    """Queue a scan for deterministic background processing."""
    _ = current_user

    scan = (
        db.query(models.Scan)
        .filter(models.Scan.id == scan_id)
        .with_for_update()
        .first()
    )

    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found.",
        )

    if scan.status in {"queued", "running"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This scan is already queued or running.",
        )

    if scan.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This scan has already completed.",
        )

    previous_status = scan.status
    job_id = str(uuid4())

    scan.job_id = job_id
    scan.status = "queued"
    scan.error_message = None
    db.commit()

    try:
        run_scan_task.apply_async(
            args=[scan.id],
            task_id=job_id,
        )
    except Exception as exc:
        scan.status = previous_status
        scan.job_id = None
        scan.error_message = (
            "The scan could not be added to the background queue."
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The background scan queue is unavailable.",
        ) from exc

    db.refresh(scan)
    return scan


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