from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db
from backend.app.intelligence.service import build_intelligence_graph


router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/graph", response_model=schemas.IntelligenceGraph)
def get_intelligence_graph(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.IntelligenceGraph:
    """Return the traceable resource-to-risk intelligence graph."""
    _ = current_user
    results = (
        db.query(models.ComplianceResult)
        .options(
            joinedload(models.ComplianceResult.resource),
            joinedload(models.ComplianceResult.policy),
            joinedload(models.ComplianceResult.scan),
        )
        .order_by(models.ComplianceResult.created_at.desc())
        .all()
    )
    return build_intelligence_graph(results)
