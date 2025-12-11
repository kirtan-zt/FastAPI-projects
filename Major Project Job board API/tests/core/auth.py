from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from tests.core.config import settings
from jose import jwt, JWTError

load_dotenv()

SECRET_KEY = settings.SECRET_KEY # Loading the API secret key
ALGORITHM = settings.ALGORITHM # Loading the encryption algorithm 
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES # Load token time expiration

pwd_context = CryptContext(schemes=["sha256_crypt", "bcrypt"], deprecated="auto")

# Verify if a plain text password matches a hashed password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Takes a password as input and returns its hashed value.
def get_password_hash(password: str) ->str:
    return pwd_context.hash(password)

# Returns an encoded JWT
def create_access_token(data: dict, expires_delta: timedelta | None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.now(timezone.utc)+expires_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Decodes a JWT token using a secret key and algorithm, extracts the username from the payload
def verify_token(token: str):
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str=payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None