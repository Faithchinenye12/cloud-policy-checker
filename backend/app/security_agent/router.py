from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db
from backend.app.security_agent.service import analyze_security


router = APIRouter(prefix="/security-agent", tags=["Security Agent"])


@router.post("/analyze", response_model=schemas.SecurityAgentResponse)
def analyze(
    payload: schemas.SecurityAgentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> schemas.SecurityAgentResponse:
    """Investigate stored evidence through a read-only Strands agent."""
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
    return analyze_security(
        payload.question,
        results,
        force_preview=bool(getattr(request.state, "demo_session", False)),
    )
