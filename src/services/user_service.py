from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.auth.password import hash_password, verify_password
from src.database import get_db_session
from src import config
from src.models import PrivacyConsent, User


class UserAlreadyExistsError(ValueError):
    pass


class InvalidPasswordError(ValueError):
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


def register_user(email, password, accept_privacy=False):
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise ValueError("Email cannot be empty.")
    if not isinstance(password, str) or len(password) < 8:
        raise InvalidPasswordError("Password must contain at least 8 characters.")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
    )

    try:
        with get_db_session() as session:
            session.add(user)
            session.flush()
            if accept_privacy:
                session.add(PrivacyConsent(user_id=user.id, policy_version=config.CURRENT_PRIVACY_POLICY_VERSION))
    except IntegrityError as exc:
        raise UserAlreadyExistsError("Email is already registered.") from exc

    return user


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
