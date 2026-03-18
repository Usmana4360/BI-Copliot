from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import text
from .models import UserCreate, UserLogin, Token
from .utils import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from backend.utils.db import get_engine

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=Token)
def register(user: UserCreate):
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    engine = get_engine()
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user.email}
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered.")
        conn.execute(
            text("INSERT INTO users (email, hashed_password) VALUES (:email, :pw)"),
            {"email": user.email, "pw": hash_password(user.password)}
        )
        conn.commit()
    token = create_access_token({"sub": user.email})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(user: UserLogin):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT hashed_password FROM users WHERE email = :email"),
            {"email": user.email}
        ).fetchone()
    if not row or not verify_password(user.password, row.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token({"sub": user.email})
    return Token(access_token=token)


# ✅ New refresh endpoint
@router.post("/refresh", response_model=Token)
def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Accept a still-valid access token and return a brand-new one.
    Frontend calls this on app load when a token exists in sessionStorage.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid.")

    # Verify user still exists and is active in DB
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM users WHERE email = :email AND is_active = TRUE"),
            {"email": email}
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found or inactive.")

    # Issue a fresh token — resets the 8-hour clock
    new_token = create_access_token({"sub": email})
    return Token(access_token=new_token)


# Reusable dependency to protect any endpoint
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")

        # Fetch role from DB
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT role FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
        role = row[0] if row else "operator"
        return {"email": email, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid.")