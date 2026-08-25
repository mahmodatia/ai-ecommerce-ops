from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.core.auth import AuthError, create_session_token, verify_credentials
from app.core.config import get_settings

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/status")
def auth_status():
    settings = get_settings()
    return {
        "required": settings.auth_mode == "password",
        "mode": settings.auth_mode,
    }


@router.post("/login")
def login(payload: LoginRequest):
    settings = get_settings()
    if settings.auth_mode != "password":
        return {"required": False, "token": None, "username": "local"}

    try:
        valid = verify_credentials(settings, payload.username, payload.password)
    except AuthError as exc:
        raise HTTPException(500, str(exc)) from exc

    if not valid:
        raise HTTPException(401, "Invalid username or password")

    return {
        "required": True,
        "token": create_session_token(settings, payload.username),
        "username": payload.username,
    }
