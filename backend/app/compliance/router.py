from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.compliance.service import build_readiness
from backend.app.dependencies import get_db

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/readiness", response_model=schemas.ComplianceReadinessResponse)
def get_readiness(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    _ = current_user
    frameworks = db.query(models.ComplianceFramework).options(joinedload(models.ComplianceFramework.controls).joinedload(models.FrameworkControl.policy_mappings)).filter(models.ComplianceFramework.is_active.is_(True)).order_by(models.ComplianceFramework.id).all()
    results = db.query(models.ComplianceResult).options(
        joinedload(models.ComplianceResult.resource),
        joinedload(models.ComplianceResult.policy),
    ).order_by(models.ComplianceResult.created_at.desc()).all()
    return build_readiness(frameworks, results)
