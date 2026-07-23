import os

from fastapi import Depends, HTTPException, Request, status

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
    request.state.user_id = user.id
    return user


def require_admin_user(user=Depends(require_current_user)):
    admin_emails = {
        email.strip().casefold()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    }
    if user.email.casefold() not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "admin_access_required", "message": "Administrator access is required."},
        )
    return user
