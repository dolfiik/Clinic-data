from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.api.deps import get_db, get_current_active_user
from app.schemas import AuditLogWithUser, AuditLogFilter
from app.services import AuditService
from app.models import User

router = APIRouter()

@router.get("/logs", response_model=list[AuditLogWithUser])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filtr po ID użytkownika"),
    action: Optional[str] = Query(None, description="Filtr po akcji"),
    table_name: Optional[str] = Query(None, description="Filtr po tabeli"),
    date_from: Optional[datetime] = Query(None, description="Data początkowa (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Data końcowa (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Limit wyników"),
    offset: int = Query(0, ge=0, description="Offset dla paginacji"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera logi audytowe z filtrami
    
    **Wymaga:** Bearer Token (admin lub własne logi)
    
    **Parametry:**
    - user_id: Opcjonalny filtr po użytkowniku
    - action: Opcjonalny filtr po akcji (np. "CREATE_PATIENT", "LOGIN")
    - table_name: Opcjonalny filtr po tabeli
    - date_from: Opcjonalna data początkowa
    - date_to: Opcjonalna data końcowa
    - limit: Maksymalna liczba wyników (domyślnie 100, max 1000)
    - offset: Offset dla paginacji
    
    **Zwraca:**
    - Lista logów z informacjami o użytkownikach
    
    **Uprawnienia:**
    - Admin: Widzi wszystkie logi
    - Inni: Widzą tylko własne logi (user_id jest wymuszony)
    """
    if current_user.role != 'admin':
        if user_id and user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own audit logs"
            )
        user_id = current_user.id
    
    filters = AuditLogFilter(
        user_id=user_id,
        action=action,
        table_name=table_name,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )
    
    return AuditService.get_logs(db, filters)

@router.get("/user/{user_id}/activity", response_model=list)
async def get_user_activity(
    user_id: int,
    limit: int = Query(50, ge=1, le=200, description="Limit wyników"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera ostatnie aktywności użytkownika
    
    **Wymaga:** Bearer Token (admin lub własne ID)
    
    **Parametry:**
    - user_id: ID użytkownika
    - limit: Maksymalna liczba wyników (domyślnie 50, max 200)
    
    **Zwraca:**
    - Lista ostatnich akcji użytkownika
    """
    if current_user.role != 'admin' and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own activity or must be admin"
        )
    
    return AuditService.get_user_activity(db, user_id, limit)

@router.get("/action/{action_type}", response_model=list[AuditLogWithUser])
async def get_logs_by_action(
    action_type: str,
    limit: int = Query(20, ge=1, le=100, description="Limit wyników"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera ostatnie logi konkretnej akcji
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Parametry:**
    - action_type: Typ akcji (np. "CREATE_PATIENT", "LOGIN", "PREDICT_TRIAGE")
    - limit: Maksymalna liczba wyników (domyślnie 20, max 100)
    
    **Zwraca:**
    - Lista logów dla danej akcji
    
    **Przykładowe akcje:**
    - LOGIN, LOGOUT, REGISTER
    - CREATE_PATIENT, UPDATE_PATIENT, DELETE_PATIENT
    - CHANGE_PATIENT_STATUS
    - PREDICT_TRIAGE
    - RECORD_OCCUPANCY
    - CHANGE_USER_ROLE, DEACTIVATE_USER, ACTIVATE_USER
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can view logs by action type"
        )
    
    return AuditService.get_recent_actions(db, action_type, limit)

@router.get("/record/{table_name}/{record_id}", response_model=list[AuditLogWithUser])
async def get_record_history(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera historię zmian konkretnego rekordu
    
    **Wymaga:** Bearer Token (admin lub doctor)
    
    **Parametry:**
    - table_name: Nazwa tabeli (patients, users, triage_predictions, department_occupancy)
    - record_id: ID rekordu
    
    **Zwraca:**
    - Pełna historia zmian rekordu (chronologicznie)
    - Każdy log zawiera:
      - Akcję (CREATE, UPDATE, DELETE, etc.)
      - Użytkownika który wykonał akcję
      - Stare wartości (przed zmianą)
      - Nowe wartości (po zmianie)
      - Timestamp
      - IP address
    """
    if current_user.role not in ['admin', 'doctor']:
        raise HTTPException(
            status_code=403,
            detail="Only admin or doctor can view record history"
        )
    
    valid_tables = ['patients', 'users', 'triage_predictions', 'department_occupancy', 'audit_log']
    if table_name not in valid_tables:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name. Must be one of: {', '.join(valid_tables)}"
        )
    
    return AuditService.get_record_history(db, table_name, record_id)

@router.get("/stats/summary")
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365, description="Liczba dni wstecz"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera statystyki logów audytowych
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Parametry:**
    - days: Liczba dni wstecz (domyślnie 30, max 365)
    
    **Zwraca:**
    - Całkowita liczba akcji
    - Top 10 najczęstszych akcji
    - Top 10 najbardziej aktywnych użytkowników
    - Okres statystyk
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can view audit statistics"
        )
    
    date_from = datetime.now() - timedelta(days=days)
    
    return AuditService.get_stats(db, date_from)

@router.get("/actions/list")
async def get_available_actions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera listę dostępnych akcji w systemie
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Lista wszystkich typów akcji z opisami
    """
    actions = {
        "authentication": [
            {"action": "LOGIN", "description": "Logowanie użytkownika"},
            {"action": "LOGOUT", "description": "Wylogowanie użytkownika"},
            {"action": "REGISTER", "description": "Rejestracja nowego użytkownika"}
        ],
        "patients": [
            {"action": "CREATE_PATIENT", "description": "Utworzenie nowego pacjenta"},
            {"action": "UPDATE_PATIENT", "description": "Aktualizacja danych pacjenta"},
            {"action": "DELETE_PATIENT", "description": "Usunięcie pacjenta"},
            {"action": "CHANGE_PATIENT_STATUS", "description": "Zmiana statusu pacjenta"}
        ],
        "triage": [
            {"action": "PREDICT_TRIAGE", "description": "Wykonanie predykcji triaży"}
        ],
        "departments": [
            {"action": "RECORD_OCCUPANCY", "description": "Zapisanie obłożenia oddziałów"}
        ],
        "users": [
            {"action": "CHANGE_USER_ROLE", "description": "Zmiana roli użytkownika"},
            {"action": "DEACTIVATE_USER", "description": "Dezaktywacja użytkownika"},
            {"action": "ACTIVATE_USER", "description": "Aktywacja użytkownika"}
        ]
    }
    
    return actions

@router.get("/recent/all")
async def get_recent_all_actions(
    limit: int = Query(50, ge=1, le=200, description="Limit wyników"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera ostatnie akcje ze wszystkich kategorii
    
    **Wymaga:** Bearer Token (admin lub własne akcje)
    
    **Parametry:**
    - limit: Maksymalna liczba wyników
    
    **Zwraca:**
    - Lista ostatnich akcji (wszystkich typów)
    """
    user_id = None if current_user.role == 'admin' else current_user.id
    
    filters = AuditLogFilter(
        user_id=user_id,
        limit=limit,
        offset=0
    )
    
    return AuditService.get_logs(db, filters)

@router.get("/timeline/{table_name}/{record_id}")
async def get_record_timeline(
    table_name: str,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera timeline zmian rekordu (uproszczona wizualizacja)
    
    **Wymaga:** Bearer Token (admin lub doctor)
    
    **Parametry:**
    - table_name: Nazwa tabeli
    - record_id: ID rekordu
    
    **Zwraca:**
    - Timeline wydarzeń z kluczowymi informacjami
    """
    if current_user.role not in ['admin', 'doctor']:
        raise HTTPException(
            status_code=403,
            detail="Only admin or doctor can view record timeline"
        )
    
    logs = AuditService.get_record_history(db, table_name, record_id)
    
    timeline = []
    for log in logs:
        event = {
            "timestamp": log.timestamp,
            "action": log.action,
            "user": log.username if log.username else "Unknown",
            "changes": []
        }
        
        if log.action == "CREATE":
            event["summary"] = f"Rekord utworzony przez {event['user']}"
        elif log.action.startswith("UPDATE"):
            if log.old_values and log.new_values:
                changes = []
                for key in log.new_values:
                    if key in log.old_values:
                        old = log.old_values[key]
                        new = log.new_values[key]
                        if old != new:
                            changes.append(f"{key}: {old} → {new}")
                event["changes"] = changes
                event["summary"] = f"Zaktualizowano {len(changes)} pól"
        elif log.action == "DELETE":
            event["summary"] = f"Rekord usunięty przez {event['user']}"
        else:
            event["summary"] = f"{log.action} wykonane przez {event['user']}"
        
        timeline.append(event)
    
    return {
        "table": table_name,
        "record_id": record_id,
        "total_events": len(timeline),
        "timeline": timeline
    }
