from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse, RefreshRequest, MessageResponse
from app.services import AuthService
from app.models import User

router = APIRouter()

def get_ip_address(request: Request) -> str:
    """Pomocnicza funkcja do pobierania IP"""
    return request.client.host if request.client else None

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Logowanie użytkownika
    
    Zwraca access_token i refresh_token dla zalogowanego użytkownika.
    
    **Parametry:**
    - email: Email użytkownika
    - password: Hasło
    
    **Zwraca:**
    - access_token: Token dostępowy (ważny 30 minut)
    - refresh_token: Token odświeżający (ważny 7 dni)
    - token_type: Typ tokena (bearer)
    """
    ip_address = get_ip_address(request)
    return AuthService.login_user(db, credentials, ip_address)

@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Rejestracja nowego użytkownika
    
    Tworzy nowe konto użytkownika i zwraca tokeny dostępowe.
    
    **Parametry:**
    - email: Email użytkownika (unikalny)
    - username: Nazwa użytkownika (unikalna)
    - password: Hasło (min. 8 znaków)
    
    **Zwraca:**
    - access_token: Token dostępowy
    - refresh_token: Token odświeżający
    - token_type: Typ tokena (bearer)
    """
    ip_address = get_ip_address(request)
    
    user = AuthService.register_user(db, user_data, ip_address)
    
    credentials = LoginRequest(email=user_data.email, password=user_data.password)
    return AuthService.login_user(db, credentials, ip_address)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Odświeżenie access tokena
    
    Generuje nowy access_token używając refresh_tokena.
    
    **Parametry:**
    - refresh_token: Refresh token otrzymany przy logowaniu
    
    **Zwraca:**
    - access_token: Nowy token dostępowy
    - refresh_token: Ten sam refresh token
    - token_type: Typ tokena (bearer)
    """
    from app.core.security import decode_token
    
    payload = decode_token(refresh_request.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    new_access_token = AuthService.refresh_access_token(db, user_id)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_request.refresh_token,
        token_type="bearer"
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Wylogowanie użytkownika
    
    Loguje akcję wylogowania w audit logu.
    W przypadku JWT, klient powinien usunąć token lokalnie.
    
    **Wymaga:** Bearer Token
    """
    from app.services.audit_service import log_action
    
    ip_address = get_ip_address(request)
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="LOGOUT",
        ip_address=ip_address
    )
    
    return MessageResponse(
        message="Successfully logged out",
        success=True
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera informacje o zalogowanym użytkowniku
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Pełne informacje o zalogowanym użytkowniku
    """
    return UserResponse.model_validate(current_user)
