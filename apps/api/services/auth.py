import hashlib
import secrets
from sqlalchemy import select
from packages.db.models import User


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def provision_user(db, display_name: str):
    token = secrets.token_urlsafe(32)
    user = User(display_name=display_name, token_hash=hash_token(token))
    db.add(user)
    db.flush()
    return user, token


def authenticate(db, token: str):
    if not 20 <= len(token) <= 200:
        return None
    return db.scalar(select(User).where(User.token_hash == hash_token(token)))
