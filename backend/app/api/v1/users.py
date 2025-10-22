from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_active_user
from app.schemas import UserResponse, UserUpdate, MessageResponse
from app.services import AuthService
from app.models import User

router = APIRouter()

def get_ip_address(request: Request) -> str:
    """Pomocnicza funkcja do pobierania IP"""
    return request.client.host if request.client else None

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera informacje o zalogowanym użytkowniku
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - ID użytkownika
    - Email
    - Username
    - Rola (admin, doctor, nurse, receptionist)
    - Status aktywności
    - Data utworzenia konta
    - Data ostatniego logowania
    """
    return UserResponse.model_validate(current_user)

@router.get("/", response_model=list[UserResponse])
async def list_users(
    role: Optional[str] = Query(None, description="Filtr po roli"),
    is_active: Optional[bool] = Query(None, description="Filtr po statusie aktywności"),
    limit: int = Query(50, ge=1, le=200, description="Limit wyników"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera listę użytkowników
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Parametry:**
    - role: Opcjonalny filtr po roli (admin, doctor, nurse, receptionist)
    - is_active: Opcjonalny filtr po statusie (true/false)
    - limit: Maksymalna liczba wyników (domyślnie 50, max 200)
    
    **Zwraca:**
    - Lista użytkowników
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can list users"
        )
    
    query = db.query(User)
    
    if role:
        valid_roles = ['admin', 'doctor', 'nurse', 'receptionist']
        if role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(User.created_at.desc()).limit(limit).all()
    
    return [UserResponse.model_validate(user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera dane użytkownika
    
    **Wymaga:** Bearer Token (admin lub własne ID)
    
    **Parametry:**
    - user_id: ID użytkownika
    
    **Zwraca:**
    - Dane użytkownika
    """
    if current_user.role != 'admin' and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own profile or must be admin"
        )
    
    user = AuthService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    new_role: str = Query(..., description="Nowa rola: admin, doctor, nurse, receptionist"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Zmienia rolę użytkownika
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Parametry:**
    - user_id: ID użytkownika
    - new_role: Nowa rola (admin, doctor, nurse, receptionist)
    
    **Zwraca:**
    - Zaktualizowany użytkownik
    
    **Uwaga:** Nie można zmienić roli samemu sobie
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can change user roles"
        )
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role"
        )
    
    ip_address = get_ip_address(request)
    
    user = AuthService.change_user_role(
        db=db,
        user_id=user_id,
        new_role=new_role,
        admin_id=current_user.id,
        ip_address=ip_address
    )
    
    return UserResponse.model_validate(user)

@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Dezaktywuje użytkownika
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Parametry:**
    - user_id: ID użytkownika do dezaktywacji
    
    **Zwraca:**
    - Zaktualizowany użytkownik
    
    **Uwaga:** 
    - Nie można dezaktywować samego siebie
    - Dezaktywowany użytkownik nie może się logować
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can deactivate users"
        )
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )
    
    ip_address = get_ip_address(request)
    
    user = AuthService.deactivate_user(
        db=db,
        user_id=user_id,
        admin_id=current_user.id,
        ip_address=ip_address
    )
    
    return UserResponse.model_validate(user)

@router.patch("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Aktywuje zdezaktywowanego użytkownika
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Parametry:**
    - user_id: ID użytkownika do aktywacji
    
    **Zwraca:**
    - Zaktualizowany użytkownik
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can activate users"
        )
    
    user = AuthService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    if user.is_active:
        raise HTTPException(
            status_code=400,
            detail="User is already active"
        )
    
    user.is_active = True
    db.commit()
    db.refresh(user)
    
    from app.services.audit_service import log_action
    ip_address = get_ip_address(request)
    
    log_action(
        db=db,
        user_id=current_user.id,
        action="ACTIVATE_USER",
        table_name="users",
        record_id=user_id,
        old_values={"is_active": False},
        new_values={"is_active": True},
        ip_address=ip_address
    )
    
    return UserResponse.model_validate(user)

@router.get("/stats/summary")
async def get_users_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera statystyki użytkowników
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Zwraca:**
    - Całkowita liczba użytkowników
    - Liczba aktywnych użytkowników
    - Liczba użytkowników według ról
    - Ostatnio zarejestrowani użytkownicy (top 5)
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can view user stats"
        )
    
    from sqlalchemy import func
    
    total_users = db.query(User).count()
    
    active_users = db.query(User).filter(User.is_active == True).count()
    
    by_role = db.query(
        User.role,
        func.count(User.id)
    ).group_by(User.role).all()
    
    role_stats = {role: count for role, count in by_role}
    
    recent_users = db.query(User).order_by(
        User.created_at.desc()
    ).limit(5).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "by_role": role_stats,
        "recent_registrations": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at
            }
            for user in recent_users
        ]
    }

@router.get("/search/query")
async def search_users(
    q: str = Query(..., min_length=2, description="Zapytanie wyszukiwania"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Wyszukuje użytkowników
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Parametry:**
    - q: Tekst do wyszukania (email lub username)
    - limit: Maksymalna liczba wyników
    
    **Zwraca:**
    - Lista znalezionych użytkowników
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can search users"
        )
    
    users = db.query(User).filter(
        (User.email.like(f"%{q}%")) |
        (User.username.like(f"%{q}%"))
    ).limit(limit).all()
    
    return [UserResponse.model_validate(user) for user in users]
