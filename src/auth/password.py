import bcrypt


def hash_password(password):
    if not isinstance(password, str) or not password:
        raise ValueError("Password cannot be empty.")

    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password, password_hash):
    if not isinstance(password, str) or not password:
        return False
    if not isinstance(password_hash, str) or not password_hash:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (TypeError, ValueError):
        return False
