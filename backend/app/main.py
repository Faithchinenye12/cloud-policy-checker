from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth.router import router as auth_router
from backend.app.policies.router import router as policy_router
from backend.app.intelligence.router import router as intelligence_router
from backend.app.resources.router import router as resource_router
from backend.app.remediations.router import router as remediation_router
from backend.app.compliance.router import router as compliance_router
from backend.app.scans.router import router as scan_router
from config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Multi-cloud security policy scanning and compliance reporting API."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def protect_demo_data(request: Request, call_next):
    """Keep the shared recruiter demo immutable while allowing normal accounts."""
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.url.path != "/auth/demo":
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            from backend.app.auth.utils import decode_access_token
            try:
                if decode_access_token(authorization[7:]).get("demo"):
                    return JSONResponse(status_code=403, content={"detail":"The public demo is read-only."})
            except Exception:
                pass
    return await call_next(request)


@app.get("/", tags=["Health"])
def read_root() -> dict:
    """Return a simple confirmation that the API is running."""
    return {
        "message": "CloudConform API is running.",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """Return an application health status for monitoring tools."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


app.include_router(auth_router)
app.include_router(policy_router)
app.include_router(resource_router)
app.include_router(scan_router)
app.include_router(intelligence_router)
app.include_router(remediation_router)
app.include_router(compliance_router)
