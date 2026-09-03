"""Idempotently seed a safe, representative portfolio workspace."""
from backend.app import models
from backend.app.auth.utils import hash_password
from backend.app.compliance.service import map_policy_to_controls
from backend.app.dependencies import SessionLocal


def seed() -> None:
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email="demo@cloudconform.app").first()
        if not user:
            db.add(models.User(email="demo@cloudconform.app", username="Recruiter Demo", hashed_password=hash_password("disabled-demo-password")))
        organization = db.query(models.Organization).filter_by(name="CloudConform Demo").first()
        if not organization:
            organization = models.Organization(name="CloudConform Demo"); db.add(organization); db.flush()
        resource = db.query(models.Resource).filter_by(cloud_id="arn:aws:s3:::cloudconform-demo-evidence").first()
        if not resource:
            resource = models.Resource(name="Customer Evidence Vault", resource_type="storage_bucket", cloud_provider="aws", cloud_id="arn:aws:s3:::cloudconform-demo-evidence", organization_id=organization.id, region="eu-west-2", configuration={"public_access_blocked":False,"encryption_enabled":True})
            db.add(resource); db.flush()
        specifications = [
            ("AWS storage buckets must block public access", "public_access_blocked"),
            ("AWS storage buckets require encryption", "encryption_enabled"),
        ]
        policies=[]
        for name, field in specifications:
            policy=db.query(models.Policy).filter_by(name=name).first()
            if not policy:
                policy=models.Policy(name=name,description=f"Validates {field} on AWS storage.",severity="high",cloud_provider="aws",resource_type="storage_bucket",rule_type="boolean_property_equals",rule_config={"field":field,"expected_value":True},is_active=True)
                db.add(policy);db.flush();map_policy_to_controls(db,policy)
            policies.append(policy)
        if not db.query(models.Scan).filter_by(job_id="cloudconform-public-demo").first():
            scan=models.Scan(organization_id=organization.id,cloud_provider="aws",resource_type="storage_bucket",job_id="cloudconform-public-demo",status="completed",total_resources=1,compliant_count=0,non_compliant_count=1)
            db.add(scan);db.flush()
            for policy in policies:
                compliant=policy.rule_config["field"]=="encryption_enabled"
                db.add(models.ComplianceResult(scan_id=scan.id,resource_id=resource.id,policy_id=policy.id,compliant=compliant,details="Configuration verified by the deterministic demo scan.",remediation_status="open" if not compliant else "resolved"))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
