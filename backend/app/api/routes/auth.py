import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, normalize_email, verify_password
from app.database.session import get_db
from app.models.models import User
from app.schemas.schemas import Token, UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger("cyber_twin.auth")


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        logger.info("Registration rejected: an account already exists for this email.")
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        email=email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role="analyst",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New account registered (user_id=%s).", user.id)
    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        # Deliberately the same log message and same HTTP response whether
        # the email doesn't exist or the password is wrong, so failed
        # logins can never be used to enumerate which emails have
        # accounts. Never logs the submitted password.
        logger.info("Login failed: invalid credentials.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        logger.info("Login rejected for user_id=%s: account disabled.", user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account does not have permission to sign in")

    logger.info("Login succeeded (user_id=%s).", user.id)
    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
