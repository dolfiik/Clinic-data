from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AuditLogBase(BaseModel):
    """Bazowe dane logu audytowego"""
    action: str
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    """Schema do tworzenia logu"""
    user_id: Optional[int] = None

class AuditLogResponse(AuditLogBase):
    """Schema odpowiedzi z logiem"""
    id: int
    user_id: Optional[int]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class AuditLogWithUser(AuditLogResponse):
    """Log z informacjami o użytkowniku"""
    username: Optional[str] = None
    user_email: Optional[str] = None

class AuditLogFilter(BaseModel):
    """Filtry do wyszukiwania logów"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    table_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
