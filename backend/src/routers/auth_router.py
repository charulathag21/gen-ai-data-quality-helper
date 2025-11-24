from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import json
import os

router = APIRouter()

# ---- JWT / Password config ----
SECRET_KEY = "e34a2d81b66f4c79932c9cc46e6e1199cbb80860af6e12d4fa3f5ec1c706ae3f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "data", "users.json")
USERS_FILE = os.path.abspath(USERS_FILE)


# ---- Pydantic models ----
class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# ---- Helper functions ----
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_users(users: dict):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---- Token user resolver ----
async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    users = load_users()
    if username not in users:
        raise credentials_exception

    return username


# SIGNUP (React calls /register)

@router.post("/register")
async def signup(user: UserCreate):
    users = load_users()

    if user.username in users:
        raise HTTPException(status_code=400, detail="Username already exists.")

    # bcrypt cannot hash >72 bytes
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password too long. Must be less than 72 characters."
        )

    hashed_pw = get_password_hash(user.password)


    users[user.username] = {
        "username": user.username,
        "hashed_password": hashed_pw,
        "created_at": datetime.utcnow().isoformat(),
    }

    save_users(users)

    return {"success": True, "message": "Signup successful."}


# LOGIN (React expects token)

@router.post("/login")
async def login(user: UserLogin):
    users = load_users()
    db_user = users.get(user.username)

    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")

    access_token = create_access_token(data={"sub": user.username})

    return {"token": access_token}


# GET CURRENT LOGGED USER

@router.get("/me")
async def read_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}
