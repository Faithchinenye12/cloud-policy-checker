from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db


router = APIRouter(prefix="/resources", tags=["Resources"])


def get_resource_or_404(
    resource_id: int,
    db: Session,
) -> models.Resource:
    """Return a resource or a clear not-found response."""
    resource = (
        db.query(models.Resource)
        .filter(models.Resource.id == resource_id)
        .first()
    )

    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )

    return resource


@router.post(
    "",
    response_model=schemas.Resource,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    resource_data: schemas.ResourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Resource:
    """Create a cloud-resource inventory record."""
    _ = current_user

    existing_resource = (
        db.query(models.Resource)
        .filter(models.Resource.cloud_id == resource_data.cloud_id)
        .first()
    )

    if existing_resource is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A resource with this cloud_id already exists.",
        )

    resource = models.Resource(**resource_data.model_dump())
    db.add(resource)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A resource with this cloud_id already exists.",
        ) from exc

    db.refresh(resource)
    return resource


@router.get("", response_model=list[schemas.Resource])
def list_resources(
    cloud_provider: Optional[schemas.CloudProvider] = None,
    resource_type: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Resource]:
    """List resource inventory records with optional filters."""
    _ = current_user

    query = db.query(models.Resource)

    if not include_inactive:
        query = query.filter(models.Resource.status == "active")

    if cloud_provider is not None:
        query = query.filter(
            models.Resource.cloud_provider == cloud_provider
        )

    if resource_type is not None:
        query = query.filter(
            models.Resource.resource_type == resource_type
        )

    return query.order_by(models.Resource.created_at.desc()).all()


@router.get("/{resource_id}", response_model=schemas.Resource)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Resource:
    """Return one cloud-resource inventory record."""
    _ = current_user
    return get_resource_or_404(resource_id, db)


@router.patch("/{resource_id}", response_model=schemas.Resource)
def update_resource(
    resource_id: int,
    resource_data: schemas.ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Resource:
    """Update editable resource inventory fields."""
    _ = current_user
    resource = get_resource_or_404(resource_id, db)
    changes = resource_data.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one resource field must be provided.",
        )

    for field_name, value in changes.items():
        setattr(resource, field_name, value)

    resource.last_discovered_at = datetime.utcnow()
    resource.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}", response_model=schemas.Resource)
def deactivate_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Resource:
    """Deactivate a resource without deleting its history."""
    _ = current_user
    resource = get_resource_or_404(resource_id, db)

    resource.status = "inactive"
    resource.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(resource)
    return resource