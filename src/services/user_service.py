from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.auth.password import hash_password, verify_password
from src.database import get_db_session
from src.models import User


class UserAlreadyExistsError(ValueError):
    pass


def normalize_email(email):
    if not isinstance(email, str):
        return ""
    return email.strip().lower()


def get_user_by_email(email):
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    with get_db_session() as session:
        return session.scalar(select(User).where(User.email == normalized_email))


def register_user(email, password):
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise ValueError("Email cannot be empty.")
    if not isinstance(password, str) or not password:
        raise ValueError("Password cannot be empty.")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
    )

    try:
        with get_db_session() as session:
            session.add(user)
            session.flush()
    except IntegrityError as exc:
        raise UserAlreadyExistsError("Email is already registered.") from exc

    return user


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
