from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status

from app.models import User
from app.schemas import UserCreate, LoginRequest, TokenResponse
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.services.audit_service import log_action

class AuthService:
    """Service do zarządzania autentykacją"""
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate, ip_address: Optional[str] = None) -> User:
        """
        Rejestruje nowego użytkownika
        
        Args:
            db: Sesja bazy danych
            user_data: Dane nowego użytkownika
            ip_address: Adres IP (dla logu)
            
        Returns:
            Utworzony użytkownik
            
        Raises:
            HTTPException: Jeśli email lub username już istnieje
        """
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=hashed_password,
            role='nurse',  # Domyślna rola
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        log_action(
            db=db,
            user_id=new_user.id,
            action="REGISTER",
            table_name="users",
            record_id=new_user.id,
            new_values={"email": new_user.email, "username": new_user.username, "role": new_user.role},
            ip_address=ip_address
        )
        
        return new_user
    
    @staticmethod
    def login_user(db: Session, credentials: LoginRequest, ip_address: Optional[str] = None) -> TokenResponse:
        """
        Loguje użytkownika
        
        Args:
            db: Sesja bazy danych
            credentials: Email i hasło
            ip_address: Adres IP (dla logu)
            
        Returns:
            TokenResponse z access_token i refresh_token
            
        Raises:
            HTTPException: Jeśli dane logowania są nieprawidłowe
        """
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        user.last_login = datetime.utcnow()
        db.commit()
        
        access_token = create_access_token(data={"sub": user.id, "role": user.role})
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        log_action(
            db=db,
            user_id=user.id,
            action="LOGIN",
            ip_address=ip_address
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Pobiera użytkownika po ID
        
        Args:
            db: Sesja bazy danych
            user_id: ID użytkownika
            
        Returns:
            Użytkownik lub None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Pobiera użytkownika po email
        
        Args:
            db: Sesja bazy danych
            email: Email użytkownika
            
        Returns:
            Użytkownik lub None
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def refresh_access_token(db: Session, user_id: int) -> str:
        """
        Odświeża access token
        
        Args:
            db: Sesja bazy danych
            user_id: ID użytkownika
            
        Returns:
            Nowy access token
            
        Raises:
            HTTPException: Jeśli użytkownik nie istnieje lub nie jest aktywny
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        return create_access_token(data={"sub": user.id, "role": user.role})
    
    @staticmethod
    def deactivate_user(db: Session, user_id: int, admin_id: int, ip_address: Optional[str] = None) -> User:
        """
        Dezaktywuje użytkownika
        
        Args:
            db: Sesja bazy danych
            user_id: ID użytkownika do dezaktywacji
            admin_id: ID admina wykonującego akcję
            ip_address: Adres IP
            
        Returns:
            Zaktualizowany użytkownik
            
        Raises:
            HTTPException: Jeśli użytkownik nie istnieje
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        db.commit()
        db.refresh(user)
        
        # Log akcji
        log_action(
            db=db,
            user_id=admin_id,
            action="DEACTIVATE_USER",
            table_name="users",
            record_id=user_id,
            old_values={"is_active": True},
            new_values={"is_active": False},
            ip_address=ip_address
        )
        
        return user
    
    @staticmethod
    def change_user_role(db: Session, user_id: int, new_role: str, admin_id: int, ip_address: Optional[str] = None) -> User:
        """
        Zmienia rolę użytkownika
        
        Args:
            db: Sesja bazy danych
            user_id: ID użytkownika
            new_role: Nowa rola (admin, doctor, nurse, receptionist)
            admin_id: ID admina wykonującego akcję
            ip_address: Adres IP
            
        Returns:
            Zaktualizowany użytkownik
            
        Raises:
            HTTPException: Jeśli użytkownik nie istnieje lub rola jest nieprawidłowa
        """
        valid_roles = ['admin', 'doctor', 'nurse', 'receptionist']
        if new_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        old_role = user.role
        user.role = new_role
        db.commit()
        db.refresh(user)
        
        # Log akcji
        log_action(
            db=db,
            user_id=admin_id,
            action="CHANGE_USER_ROLE",
            table_name="users",
            record_id=user_id,
            old_values={"role": old_role},
            new_values={"role": new_role},
            ip_address=ip_address
        )
        
        return user
