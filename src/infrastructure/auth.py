from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", " ") # Should be improved for production use
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()


USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$8TtJjjKQ.6ihs9Vp4oS8cOUgllCoDxQhbpx6.NlRtsHXnJJUWMiM6", #admin123
        "role": "admin"
    },
    "doctor": {
        "username": "doctor",
        "hashed_password": "$2b$12$zXUfcNJu7bJ4p203ZhhOO.cgY5RMAZvzG9svrMwmYmyZxwPXX03RC",  # doctor123
        "role": "user"
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = USERS_DB.get(username)
    if not user:
        print(f"User not found: {username}")
        return None
    
    if not verify_password(password, user["hashed_password"]):
        print(f"Invalid password for user: {username}")
        return None
    
    print(f"User authenticated: {username}")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user still exists
        user = USERS_DB.get(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"username": username, "role": user["role"]}
    
    except JWTError as e:
        print(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(user_data: dict = Depends(verify_token)) -> dict:
    return user_data

def generate_user_hash(username: str, password: str):
    hashed = get_password_hash(password)
    print(f"""
    "{username}": {{
        "username": "{username}",
        "hashed_password": "{hashed}",
        "role": "user"
    }}
    """)