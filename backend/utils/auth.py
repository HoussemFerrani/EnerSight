"""
User authentication and management utilities
"""
import hashlib
import os
import base64
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing with PBKDF2 (built-in to Python, no external dependencies)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Hash format: salt:hash
        parts = hashed_password.split(':')
        if len(parts) != 2:
            return False
        salt = base64.b64decode(parts[0].encode())
        stored_hash = parts[1]
        
        # Hash the plain password with the same salt
        new_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt, 100000)
        new_hash_b64 = base64.b64encode(new_hash).decode()
        
        return new_hash_b64 == stored_hash
    except:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using PBKDF2"""
    # Generate a random salt
    salt = os.urandom(32)
    
    # Hash the password
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
   
    # Return salt:hash (both base64 encoded)
    salt_b64 = base64.b64encode(salt).decode()
    hash_b64 = base64.b64encode(pw_hash).decode()
    
    return f"{salt_b64}:{hash_b64}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
