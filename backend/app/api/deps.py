from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Pobiera aktualnie zalogowanego użytkownika na podstawie JWT tokena
    
    Args:
        db: Sesja bazy danych
        token: JWT token z headera Authorization
        
    Returns:
        User: Obiekt zalogowanego użytkownika
        
    Raises:
        HTTPException: 401 jeśli token jest nieprawidłowy lub użytkownik nie istnieje
    """
    print(f"🔍 BACKEND - Otrzymany token: {token[:50]}..." if token else "🔍 BACKEND - BRAK TOKENA")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = int(payload.get("sub"))
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Sprawdza czy użytkownik jest aktywny
    
    Args:
        current_user: Zalogowany użytkownik z get_current_user
        
    Returns:
        User: Aktywny użytkownik
        
    Raises:
        HTTPException: 400 jeśli konto jest nieaktywne
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
