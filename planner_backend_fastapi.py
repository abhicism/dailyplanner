# Minimal backend for the Daily Planner
# Framework: FastAPI
# Run: uvicorn planner_backend_fastapi:app --reload

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt, JWTError
from sqlmodel import Field, SQLModel, create_engine, Session, select

# ---------------- CONFIG ----------------
SECRET_KEY = "change_this_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

app = FastAPI(title="Planner Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow your HTML file
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
engine = create_engine("sqlite:///planner.db", echo=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ---------------- MODELS ----------------
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

class DayEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    date_key: str = Field(index=True)
    payload: str  # JSON string from frontend
    created_at: datetime = Field(default_factory=datetime.utcnow)

SQLModel.metadata.create_all(engine)

# ---------------- SCHEMAS ----------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Register(BaseModel):
    username: str
    password: str

class SaveDay(BaseModel):
    date_key: str
    payload: dict

# ---------------- AUTH HELPERS ----------------
import bcrypt

def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

# ---------------- ROUTES ----------------
@app.post("/register")
def register(data: Register):
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == data.username)).first()
        if existing:
            raise HTTPException(400, "Username exists")
        user = User(username=data.username, hashed_password=hash_password(data.password))
        session.add(user)
        session.commit()
        return {"msg": "registered"}

@app.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form.username)).first()
        if not user or not verify_password(form.password, user.hashed_password):
            raise HTTPException(401, "Invalid credentials")
        token = create_token({"sub": user.username})
        return {"access_token": token}

@app.post("/save_day")
def save_day(data: SaveDay, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        existing = session.exec(select(DayEntry).where(DayEntry.user_id==user.id, DayEntry.date_key==data.date_key)).first()
        if existing:
            existing.payload = str(data.payload)
        else:
            entry = DayEntry(user_id=user.id, date_key=data.date_key, payload=str(data.payload))
            session.add(entry)
        session.commit()
        return {"msg": "saved"}

@app.get("/get_day/{date_key}")
def get_day(date_key: str, user: User = Depends(get_current_user)):
    with Session(engine) as session:
        entry = session.exec(select(DayEntry).where(DayEntry.user_id==user.id, DayEntry.date_key==date_key)).first()
        return {"data": entry.payload if entry else None}

@app.get("/history")
def history(user: User = Depends(get_current_user)):
    with Session(engine) as session:
        entries = session.exec(select(DayEntry).where(DayEntry.user_id==user.id)).all()
        return [{"date_key": e.date_key, "payload": e.payload} for e in entries]
