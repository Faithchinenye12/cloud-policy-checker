from datetime import datetime
from typing import Any

from backend.app import models
from backend.app.dependencies import SessionLocal
from backend.app.policies.engine import evaluate_policy
from backend.app.providers.aws import AwsDiscoveryError, sync_s3_inventory
from backend.app.providers.azure import AzureDiscoveryError, sync_azure_inventory
from backend.app.providers.gcp import GcpDiscoveryError, sync_gcp_inventory
from config import settings


def execute_scan(scan_id: int) -> dict[str, Any]:
    """
    Execute one queued scan using its own database session.

    This function contains no FastAPI request logic, so a Celery worker can
    call it safely in a separate background process.
    """
    db = SessionLocal()

    try:
        scan = (
            db.query(models.Scan)
            .filter(models.Scan.id == scan_id)
            .first()
        )

        if scan is None:
            return {
                "scan_id": scan_id,
                "status": "missing",
            }

        if scan.status in {"running", "completed"}:
            return {
                "scan_id": scan.id,
                "status": scan.status,
            }

        scan.status = "running"
        scan.started_at = datetime.utcnow()
        scan.completed_at = None
        scan.error_message = None
        scan.total_resources = 0
        scan.compliant_count = 0
        scan.non_compliant_count = 0
        db.commit()

        if scan.cloud_provider == "aws" and settings.AWS_DISCOVERY_ENABLED:
            sync_s3_inventory(db)
        elif scan.cloud_provider == "azure" and settings.AZURE_DISCOVERY_ENABLED:
            sync_azure_inventory(db, settings.AZURE_SUBSCRIPTION_ID)
        elif scan.cloud_provider == "gcp" and settings.GCP_DISCOVERY_ENABLED:
            sync_gcp_inventory(db, settings.GCP_PROJECT_ID)

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

        (
            db.query(models.ComplianceResult)
            .filter(models.ComplianceResult.scan_id == scan.id)
            .delete(synchronize_session=False)
        )

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
                db.add(
                    models.ComplianceResult(
                        scan_id=scan.id,
                        resource_id=resource.id,
                        policy_id=evaluation.policy_id,
                        compliant=evaluation.compliant,
                        details=evaluation.details,
                    )
                )

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

        return {
            "scan_id": scan.id,
            "status": scan.status,
            "total_resources": scan.total_resources,
            "compliant_count": scan.compliant_count,
            "non_compliant_count": scan.non_compliant_count,
        }

    except Exception as exc:
        db.rollback()

        failed_scan = (
            db.query(models.Scan)
            .filter(models.Scan.id == scan_id)
            .first()
        )

        if failed_scan is not None:
            failed_scan.status = "failed"
            failed_scan.completed_at = datetime.utcnow()
            failed_scan.error_message = (
                str(exc)
                if isinstance(
                    exc,
                    (AwsDiscoveryError, AzureDiscoveryError, GcpDiscoveryError),
                )
                else "The background scan could not be completed."
            )
            db.commit()

        raise

    finally:
        db.close()
