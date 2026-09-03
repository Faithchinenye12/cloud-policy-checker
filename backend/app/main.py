from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.auth.router import router as auth_router
from backend.app.policies.router import router as policy_router
from backend.app.intelligence.router import router as intelligence_router
from backend.app.resources.router import router as resource_router
from backend.app.remediations.router import router as remediation_router
from backend.app.scans.router import router as scan_router
from config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Multi-cloud security policy scanning and compliance reporting API."
    ),
)


allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
