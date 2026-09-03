from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.app import models, schemas
from backend.app.auth.utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.app.dependencies import get_db
from config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/demo", response_model=schemas.Token)
def demo_login(db: Session = Depends(get_db)) -> schemas.Token:
    """Issue a read-only portfolio session when public demo mode is enabled."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo mode is not enabled.")
    user = db.query(models.User).filter(models.User.email == "demo@cloudconform.app").first()
    if user is None:
        user = models.User(email="demo@cloudconform.app", username="Recruiter Demo", hashed_password=hash_password("disabled-demo-password"))
        db.add(user); db.commit(); db.refresh(user)
    return schemas.Token(access_token=create_access_token(user.email, extra_claims={"demo": True}), token_type="bearer")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Read the signed bearer token and return its authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


@router.post(
    "/register",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
) -> models.User:
    """Create a new user account with a securely hashed password."""
    if settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled in the public demo.")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already in use.",
        )

    new_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=schemas.Token)
def login_user(
    credentials: schemas.UserLogin,
    db: Session = Depends(get_db),
) -> schemas.Token:
    """Validate user credentials and return a signed access token."""
    user = db.query(models.User).filter(
        models.User.email == credentials.email
    ).first()

    if user is None or not verify_password(
        credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    return schemas.Token(
        access_token=create_access_token(user.email),
        token_type="bearer",
    )


@router.get("/me", response_model=schemas.User)
def read_current_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Return the currently authenticated user."""
    return current_user
