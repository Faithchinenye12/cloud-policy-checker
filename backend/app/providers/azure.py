from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app import models


class AzureDiscoveryError(RuntimeError):
    """Raised when Azure inventory cannot be read safely."""


@dataclass(frozen=True)
class AzureResourceRecord:
    name: str
    resource_type: str
    cloud_id: str
    region: str
    configuration: dict[str, Any]


def discover_storage_accounts(
    client: Optional[Any] = None,
    subscription_id: str = "",
) -> list[AzureResourceRecord]:
    """Discover Azure storage accounts and policy-relevant settings."""
    if client is None:
        if not subscription_id:
            raise AzureDiscoveryError("An Azure subscription ID is not configured.")

        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.storage import StorageManagementClient

            credential = DefaultAzureCredential()
            client = StorageManagementClient(credential, subscription_id)
        except Exception as exc:
            raise AzureDiscoveryError(
                "Azure credentials or storage account read permission are unavailable."
            ) from exc

    try:
        accounts = list(client.storage_accounts.list())
    except Exception as exc:
        raise AzureDiscoveryError(
            "Azure credentials or storage account read permission are unavailable."
        ) from exc

    records = []
    for account in accounts:
        encryption = getattr(account, "encryption", None)
        services = getattr(encryption, "services", None)
        blob = getattr(services, "blob", None)
        encryption_enabled = bool(getattr(blob, "enabled", False))

        records.append(
            AzureResourceRecord(
                name=account.name,
                resource_type="storage_account",
                cloud_id=account.id,
                region=getattr(account, "location", None) or "unknown",
                configuration={
                    "public_access_blocked": (
                        getattr(account, "allow_blob_public_access", None) is not True
                    ),
                    "encryption_enabled": encryption_enabled,
                    "minimum_tls_version": (
                        getattr(account, "minimum_tls_version", None) or "unknown"
                    ),
                    "discovery_complete": True,
                    "discovery_errors": [],
                },
            )
        )

    return records


def sync_azure_inventory(
    db: Session,
    subscription_id: str,
) -> list[models.Resource]:
    records = discover_storage_accounts(subscription_id=subscription_id)
    return _sync_records(db, records)


def _sync_records(
    db: Session,
    records: list[AzureResourceRecord],
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
        resource.cloud_provider = "azure"
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
