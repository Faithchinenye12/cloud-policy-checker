from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app import models


class GcpDiscoveryError(RuntimeError):
    """Raised when Google Cloud inventory cannot be read safely."""


@dataclass(frozen=True)
class GcpResourceRecord:
    name: str
    resource_type: str
    cloud_id: str
    region: str
    configuration: dict[str, Any]


def discover_storage_buckets(
    client: Optional[Any] = None,
    project_id: str = "",
) -> list[GcpResourceRecord]:
    """Discover Cloud Storage buckets and policy-relevant settings."""
    if client is None:
        if not project_id:
            raise GcpDiscoveryError("A Google Cloud project ID is not configured.")

        try:
            from google.cloud import storage

            client = storage.Client(project=project_id)
        except Exception as exc:
            raise GcpDiscoveryError(
                "Google Cloud credentials or bucket read permission are unavailable."
            ) from exc

    try:
        buckets = list(client.list_buckets(project=project_id or None))
    except Exception as exc:
        raise GcpDiscoveryError(
            "Google Cloud credentials or bucket read permission are unavailable."
        ) from exc

    records = []
    for bucket in buckets:
        iam = getattr(bucket, "iam_configuration", None)
        prevention = getattr(iam, "public_access_prevention", None)
        kms_key = getattr(bucket, "default_kms_key_name", None)

        records.append(
            GcpResourceRecord(
                name=bucket.name,
                resource_type="storage_bucket",
                cloud_id=f"//storage.googleapis.com/{bucket.name}",
                region=getattr(bucket, "location", None) or "unknown",
                configuration={
                    "public_access_blocked": prevention == "enforced",
                    "encryption_enabled": True,
                    "customer_managed_encryption": bool(kms_key),
                    "uniform_bucket_level_access": bool(
                        getattr(iam, "uniform_bucket_level_access_enabled", False)
                    ),
                    "discovery_complete": True,
                    "discovery_errors": [],
                },
            )
        )

    return records


def sync_gcp_inventory(db: Session, project_id: str) -> list[models.Resource]:
    records = discover_storage_buckets(project_id=project_id)
    return _sync_records(db, records)


def _sync_records(
    db: Session,
    records: list[GcpResourceRecord],
) -> list[models.Resource]:
    now = datetime.utcnow()
    resources = []

    for record in records:
        resource = db.query(models.Resource).filter(
            models.Resource.cloud_id == record.cloud_id
        ).first()
        if resource is None:
            resource = models.Resource(
                cloud_id=record.cloud_id,
                first_discovered_at=now,
            )
            db.add(resource)

        resource.name = record.name
        resource.resource_type = record.resource_type
        resource.cloud_provider = "gcp"
        resource.region = record.region
        resource.configuration = record.configuration
        resource.status = "active"
        resource.last_discovered_at = now
        resource.updated_at = now
        resources.append(resource)

    db.commit()
    for resource in resources:
        db.refresh(resource)
    return resources
