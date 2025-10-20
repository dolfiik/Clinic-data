from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Logowanie użytkownika"""
    # TODO: Implementacja
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login endpoint not implemented yet"
    )

@router.post("/register", response_model=TokenResponse)
async def register(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Rejestracja nowego użytkownika"""
    # TODO: Implementacja
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Register endpoint not implemented yet"
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token():
    """Odświeżenie access tokena"""
    # TODO: Implementacja
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh endpoint not implemented yet"
    )
