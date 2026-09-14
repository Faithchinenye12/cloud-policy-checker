import hashlib
from datetime import datetime, timezone

import redis
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload

from backend.app import models, schemas
from backend.app.auth.router import get_current_user
from backend.app.dependencies import get_db
from backend.app.security_agent.service import analyze_security
from config import settings


router = APIRouter(prefix="/security-agent", tags=["Security Agent"])


def _demo_may_use_bedrock(request: Request) -> bool:
    """Allow a small daily quota; fall back safely if Redis is unavailable."""
    if not getattr(request.state, "demo_session", False):
        return True

    limit = settings.SECURITY_AGENT_DEMO_DAILY_LIMIT
    global_limit = settings.SECURITY_AGENT_GLOBAL_DAILY_LIMIT
    if limit == 0 or global_limit == 0:
        return False

    forwarded = request.headers.get("x-forwarded-for", "")
    client_address = forwarded.split(",", 1)[0].strip()
    if not client_address and request.client:
        client_address = request.client.host
    visitor = hashlib.sha256(client_address.encode()).hexdigest()[:24]
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    visitor_key = f"cloudconform:security-agent:{day}:{visitor}"
    global_key = f"cloudconform:security-agent:{day}:global"

    try:
        cache = redis.Redis.from_url(settings.REDIS_URL)
        pipeline = cache.pipeline()
        pipeline.incr(visitor_key)
        pipeline.incr(global_key)
        visitor_count, global_count = pipeline.execute()
        if visitor_count == 1:
            cache.expire(visitor_key, 172800)
        if global_count == 1:
            cache.expire(global_key, 172800)
        return visitor_count <= limit and global_count <= global_limit
    except redis.RedisError:
        return False


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
    demo_session = bool(getattr(request.state, "demo_session", False))
    force_preview = demo_session and (
        settings.SECURITY_AGENT_MODE != "strands" or not _demo_may_use_bedrock(request)
    )
    return analyze_security(
        payload.question,
        results,
        force_preview=force_preview,
    )
