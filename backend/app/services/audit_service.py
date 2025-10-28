from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from app.models import AuditLog, User
from app.schemas import AuditLogCreate, AuditLogResponse, AuditLogWithUser, AuditLogFilter

def convert_decimals(obj: Any) -> Any:
    """Konwertuje Decimal na float dla JSON serializacji"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj

def log_action(
    db: Session,
    user_id: Optional[int] = None,
    action: str = "",
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """
    Loguje akcję użytkownika
    
    Args:
        db: Sesja bazy danych
        user_id: ID użytkownika wykonującego akcję
        action: Nazwa akcji (np. "CREATE_PATIENT", "LOGIN")
        table_name: Nazwa tabeli (opcjonalne)
        record_id: ID rekordu (opcjonalne)
        old_values: Stare wartości (dla UPDATE)
        new_values: Nowe wartości
        ip_address: Adres IP użytkownika
        user_agent: User agent przeglądarki
        
    Returns:
        Utworzony log
    """
    if old_values:
       old_values = convert_decimals(old_values)
    if new_values:
        new_values = convert_decimals(new_values)
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return log

class AuditService:
    """Service do zarządzania logami audytowymi"""
    
    @staticmethod
    def get_logs(
        db: Session,
        filters: AuditLogFilter
    ) -> List[AuditLogWithUser]:
        """
        Pobiera logi z filtrami
        
        Args:
            db: Sesja bazy danych
            filters: Filtry wyszukiwania
            
        Returns:
            Lista logów z informacjami o użytkownikach
        """
        query = db.query(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)
        
        if filters.user_id:
            query = query.filter(AuditLog.user_id == filters.user_id)
        
        if filters.action:
            query = query.filter(AuditLog.action == filters.action)
        
        if filters.table_name:
            query = query.filter(AuditLog.table_name == filters.table_name)
        
        if filters.date_from:
            query = query.filter(AuditLog.timestamp >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(AuditLog.timestamp <= filters.date_to)
        
        query = query.order_by(AuditLog.timestamp.desc())
        
        query = query.offset(filters.offset).limit(filters.limit)
        
        logs = query.all()
        
        result = []
        for log in logs:
            log_dict = log.to_dict()
            if log.user:
                log_dict['username'] = log.user.username
                log_dict['user_email'] = log.user.email
            
            result.append(AuditLogWithUser(**log_dict))
        
        return result
    
    @staticmethod
    def get_user_activity(db: Session, user_id: int, limit: int = 50) -> List[AuditLogResponse]:
        """
        Pobiera ostatnie aktywności użytkownika
        
        Args:
            db: Sesja bazy danych
            user_id: ID użytkownika
            limit: Limit wyników
            
        Returns:
            Lista logów użytkownika
        """
        logs = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
        
        return [AuditLogResponse.model_validate(log) for log in logs]
    
    @staticmethod
    def get_recent_actions(db: Session, action_type: str, limit: int = 20) -> List[AuditLogWithUser]:
        """
        Pobiera ostatnie akcje danego typu
        
        Args:
            db: Sesja bazy danych
            action_type: Typ akcji (np. "CREATE_PATIENT")
            limit: Limit wyników
            
        Returns:
            Lista logów
        """
        logs = db.query(AuditLog).join(
            User, AuditLog.user_id == User.id, isouter=True
        ).filter(
            AuditLog.action == action_type
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
        
        result = []
        for log in logs:
            log_dict = log.to_dict()
            if log.user:
                log_dict['username'] = log.user.username
                log_dict['user_email'] = log.user.email
            
            result.append(AuditLogWithUser(**log_dict))
        
        return result
    
    @staticmethod
    def get_record_history(db: Session, table_name: str, record_id: int) -> List[AuditLogWithUser]:
        """
        Pobiera historię zmian konkretnego rekordu
        
        Args:
            db: Sesja bazy danych
            table_name: Nazwa tabeli
            record_id: ID rekordu
            
        Returns:
            Lista wszystkich zmian rekordu
        """
        logs = db.query(AuditLog).join(
            User, AuditLog.user_id == User.id, isouter=True
        ).filter(
            AuditLog.table_name == table_name,
            AuditLog.record_id == record_id
        ).order_by(
            AuditLog.timestamp.asc()  # Od najstarszej do najnowszej
        ).all()
        
        result = []
        for log in logs:
            log_dict = log.to_dict()
            if log.user:
                log_dict['username'] = log.user.username
                log_dict['user_email'] = log.user.email
            
            result.append(AuditLogWithUser(**log_dict))
        
        return result
    
    @staticmethod
    def get_stats(db: Session, date_from: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Pobiera statystyki logów
        
        Args:
            db: Sesja bazy danych
            date_from: Data od której liczyć statystyki
            
        Returns:
            Słownik ze statystykami
        """
        from sqlalchemy import func
        
        query = db.query(AuditLog)
        
        if date_from:
            query = query.filter(AuditLog.timestamp >= date_from)
        
        total_actions = query.count()
        
        actions_count = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        active_users = db.query(
            User.username,
            func.count(AuditLog.id).label('count')
        ).join(
            AuditLog, User.id == AuditLog.user_id
        ).group_by(User.username).order_by(func.count(AuditLog.id).desc()).limit(10).all()
        
        return {
            "total_actions": total_actions,
            "top_actions": [{"action": action, "count": count} for action, count in actions_count],
            "most_active_users": [{"username": username, "actions": count} for username, count in active_users],
            "period_start": date_from.isoformat() if date_from else None
        }
