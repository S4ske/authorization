from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.hash import pbkdf2_sha256

from app.core.config import settings
from enum import StrEnum


class TokenType(StrEnum):
    ACCESS = 'ACCESS'
    REFRESH = 'REFRESH'


TOKEN_TYPE_STRING = 'type'
TOKEN_EXPIRE_STRING = 'exp'
TOKEN_SUBJECT_STRING = 'sub'


def encode_jwt(to_encode: dict[str, Any]) -> str:
    return jwt.encode(to_encode, algorithm=settings.JWT_ALGORITHM, key=settings.JWT_SECRET_KEY)


def create_jwt(token_type: str, sub: Any, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {TOKEN_EXPIRE_STRING: expire, TOKEN_SUBJECT_STRING: sub, TOKEN_TYPE_STRING: token_type}
    encoded_jwt = encode_jwt(to_encode)
    return encoded_jwt


def create_access_token(sub: Any) -> str:
    return create_jwt(TokenType.ACCESS, sub, settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(sub: Any) -> str:
    return create_jwt(TokenType.REFRESH, sub, settings.REFRESH_TOKEN_EXPIRE_MINUTES)


def decode_jwt_token(token: str) -> Any:
    return jwt.decode(token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def get_secret_hash(secret: str) -> str:
    return pbkdf2_sha256.hash(secret)


def verify_secret_hash(secret: str, hashed_secret: str) -> bool:
    return pbkdf2_sha256.verify(secret, hashed_secret)
