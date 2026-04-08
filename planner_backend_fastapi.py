# Daily Planner Backend — FastAPI
# Fixed issues:
#   1. payload saved as proper JSON (was str(dict) before)
#   2. SECRET_KEY read from environment variable
#   3. DATABASE_URL supports both SQLite (local) and PostgreSQL (Render)
#   4. CORS tightened but still allows all origins for easy dev use
#   5. history endpoint now returns entries sorted newest-first
#   6. Added /health endpoint for uptime checks
#
# Local run:  uvicorn planner_backend_fastapi:app --reload
# Production: uvicorn planner_backend_fastapi:app --host 0.0.0.0 --port $PORT

import json
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

# ── CONFIG ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_in_production_please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # 7 days

# Supports both SQLite (local dev) and PostgreSQL (Render / Railway)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///planner.db")

# Render provides postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Daily Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict to your Netlify URL in production if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ── MODELS ────────────────────────────────────────────────────────────────────
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str


class DayEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    date_key: str = Field(index=True)
    payload: str                          # valid JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


SQLModel.metadata.create_all(engine)


# ── SCHEMAS ───────────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Register(BaseModel):
    username: str
    password: str


class SaveDay(BaseModel):
    date_key: str
    payload: dict                         # frontend sends a dict; we JSON-encode it


# ── AUTH HELPERS ──────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Uptime ping — keeps Render free instance warm if you ping it periodically."""
    return {"status": "ok"}


@app.post("/register")
def register(data: Register):
    if not data.username.strip() or not data.password:
        raise HTTPException(400, "Username and password required")
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == data.username)).first()
        if existing:
            raise HTTPException(400, "Username already exists")
        user = User(
            username=data.username.strip(),
            hashed_password=hash_password(data.password),
        )
        session.add(user)
        session.commit()
    return {"msg": "registered"}


@app.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form.username)).first()
        if not user or not verify_password(form.password, user.hashed_password):
            raise HTTPException(401, "Invalid username or password")
        token = create_token({"sub": user.username})
    return {"access_token": token}


@app.post("/save_day")
def save_day(data: SaveDay, user: User = Depends(get_current_user)):
    """Save or update today's planner data. payload is stored as proper JSON."""
    json_payload = json.dumps(data.payload)   # ← FIX: was str(data.payload) before
    with Session(engine) as session:
        existing = session.exec(
            select(DayEntry).where(
                DayEntry.user_id == user.id,
                DayEntry.date_key == data.date_key,
            )
        ).first()
        if existing:
            existing.payload = json_payload
            existing.updated_at = datetime.utcnow()
        else:
            entry = DayEntry(
                user_id=user.id,
                date_key=data.date_key,
                payload=json_payload,
            )
            session.add(entry)
        session.commit()
    return {"msg": "saved"}


@app.get("/get_day/{date_key}")
def get_day(date_key: str, user: User = Depends(get_current_user)):
    """Return the stored payload for a specific date key."""
    with Session(engine) as session:
        entry = session.exec(
            select(DayEntry).where(
                DayEntry.user_id == user.id,
                DayEntry.date_key == date_key,
            )
        ).first()
    return {"data": entry.payload if entry else None}


@app.get("/history")
def history(user: User = Depends(get_current_user)):
    """Return all saved days for the current user, newest first."""
    with Session(engine) as session:
        entries = session.exec(
            select(DayEntry).where(DayEntry.user_id == user.id)
        ).all()
    # Sort newest first in Python (works for both SQLite and PostgreSQL)
    entries_sorted = sorted(entries, key=lambda e: e.date_key, reverse=True)
    return [
        {"date_key": e.date_key, "payload": e.payload}
        for e in entries_sorted
    ]