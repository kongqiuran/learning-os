from fastapi import HTTPException, Request, status

from src.services.user_service import get_user_by_email


def require_current_user(request: Request):
    email = request.session.get("user_email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "authentication_required", "message": "Please sign in to continue."},
        )

    user = get_user_by_email(email)
    if user is None:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "session_expired", "message": "Your session has expired."},
        )
    return user
