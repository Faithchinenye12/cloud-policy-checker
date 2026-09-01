from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from sqlalchemy.orm import Session

from backend.app import models


class AwsDiscoveryError(RuntimeError):
    """Raised when AWS inventory cannot be read safely."""


@dataclass(frozen=True)
class AwsResourceRecord:
    name: str
    resource_type: str
    cloud_id: str
    region: str
    configuration: dict[str, Any]


def discover_s3_buckets(s3_client: Optional[Any] = None) -> list[AwsResourceRecord]:
    """Discover S3 buckets and the security settings used by policies."""
    client = s3_client or boto3.client("s3")

    try:
        buckets = client.list_buckets().get("Buckets", [])
    except (BotoCoreError, ClientError, NoCredentialsError) as exc:
        raise AwsDiscoveryError(
            "AWS credentials or s3:ListAllMyBuckets permission are unavailable."
        ) from exc

    records = []
    for bucket in buckets:
        name = bucket["Name"]
        region, region_error = _read_region(client, name)
        public_block, public_error = _read_public_access_block(client, name)
        encrypted, encryption_error = _read_encryption(client, name)
        errors = [error for error in (region_error, public_error, encryption_error) if error]

        records.append(
            AwsResourceRecord(
                name=name,
                resource_type="storage_bucket",
                cloud_id=f"arn:aws:s3:::{name}",
                region=region,
                configuration={
                    "public_access_blocked": public_block,
                    "encryption_enabled": encrypted,
                    "discovery_complete": not errors,
                    "discovery_errors": errors,
                },
            )
        )

    return records


def sync_s3_inventory(db: Session) -> list[models.Resource]:
    """Upsert discovered S3 buckets without deleting historical inventory."""
    discovered = discover_s3_buckets()
    now = datetime.utcnow()
    resources = []

    for record in discovered:
        resource = db.query(models.Resource).filter(
            models.Resource.cloud_id == record.cloud_id
        ).first()

        if resource is None:
            resource = models.Resource(
                name=record.name,
                resource_type=record.resource_type,
                cloud_provider="aws",
                cloud_id=record.cloud_id,
                region=record.region,
                configuration=record.configuration,
                status="active",
                first_discovered_at=now,
                last_discovered_at=now,
            )
            db.add(resource)
        else:
            resource.name = record.name
            resource.resource_type = record.resource_type
            resource.cloud_provider = "aws"
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


def _read_region(client: Any, bucket: str) -> tuple[str, Optional[str]]:
    try:
        location = client.get_bucket_location(Bucket=bucket).get("LocationConstraint")
        return location or "us-east-1", None
    except (BotoCoreError, ClientError) as exc:
        return "unknown", _safe_error("region", exc)


def _read_public_access_block(client: Any, bucket: str) -> tuple[bool, Optional[str]]:
    try:
        configuration = client.get_public_access_block(
            Bucket=bucket
        )["PublicAccessBlockConfiguration"]
        fields = (
            "BlockPublicAcls",
            "IgnorePublicAcls",
            "BlockPublicPolicy",
            "RestrictPublicBuckets",
        )
        return all(configuration.get(field, False) for field in fields), None
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        if code in {"NoSuchPublicAccessBlockConfiguration", "NoSuchPublicAccessBlock"}:
            return False, None
        return False, _safe_error("public access block", exc)
    except BotoCoreError as exc:
        return False, _safe_error("public access block", exc)


def _read_encryption(client: Any, bucket: str) -> tuple[bool, Optional[str]]:
    try:
        rules = client.get_bucket_encryption(Bucket=bucket).get(
            "ServerSideEncryptionConfiguration", {}
        ).get("Rules", [])
        return bool(rules), None
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        if code == "ServerSideEncryptionConfigurationNotFoundError":
            return False, None
        return False, _safe_error("encryption", exc)
    except BotoCoreError as exc:
        return False, _safe_error("encryption", exc)


def _safe_error(setting: str, error: Exception) -> str:
    if isinstance(error, ClientError):
        code = error.response.get("Error", {}).get("Code", "Unknown")
        return f"Could not read {setting}: {code}."
    return f"Could not read {setting}."
