from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.api.dependencies import require_current_user
from src.api.schemas import AuthResponse, LoginRequest, MessageResponse, RegisterRequest
from src.services.user_service import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    authenticate_user,
    register_user,
)
from src.logging_config import get_logger


router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = get_logger(__name__)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=400,
            detail={"code": "password_mismatch", "message": "The passwords do not match."},
        )
    if not payload.accepted_terms:
        raise HTTPException(
            status_code=400,
            detail={"code": "terms_consent_required", "message": "Privacy policy and terms must be accepted."},
        )
    try:
        user = register_user(payload.email, payload.password, accept_privacy=True)
    except UserAlreadyExistsError as exc:
        logger.warning(
            "Registration rejected because the account already exists.",
            extra={"event": "auth.register.rejected", "exception": exc},
        )
        raise HTTPException(
            status_code=409,
            detail={"code": "email_registered", "message": "This email is already registered."},
        ) from exc
    except InvalidPasswordError as exc:
        logger.warning(
            "Registration rejected because the password policy was not met.",
            extra={"event": "auth.register.rejected", "exception": exc},
        )
        raise HTTPException(
            status_code=400,
            detail={"code": "weak_password", "message": str(exc)},
        ) from exc
    except ValueError as exc:
        logger.warning(
            "Registration rejected because the request was invalid.",
            extra={"event": "auth.register.rejected", "exception": exc},
        )
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_registration", "message": str(exc)},
        ) from exc

    request.session["user_email"] = user.email
    request.state.user_id = user.id
    logger.info(
        "User registration completed.",
        extra={"event": "auth.register.success", "user_id": user.id},
    )
    return AuthResponse(user=user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request):
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        logger.warning(
            "Login rejected because credentials were invalid.",
            extra={"event": "auth.login.rejected"},
        )
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": "The email or password is incorrect."},
        )
    request.session["user_email"] = user.email
    request.state.user_id = user.id
    logger.info(
        "User login completed.",
        extra={"event": "auth.login.success", "user_id": user.id},
    )
    return AuthResponse(user=user)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request):
    request.session.clear()
    return MessageResponse(message="Signed out successfully.")


@router.get("/me", response_model=AuthResponse)
def get_current_user(user=Depends(require_current_user)):
    return AuthResponse(user=user)
