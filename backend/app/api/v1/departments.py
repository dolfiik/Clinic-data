from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_active_user
from app.schemas import (
    DepartmentOccupancyCreate,
    DepartmentOccupancyResponse,
    CurrentOccupancyResponse,
    OccupancyHistory,
    DepartmentStats,
    MessageResponse
)
from app.services import DepartmentService
from app.models import User

router = APIRouter()

def get_ip_address(request: Request) -> str:
    """Pomocnicza funkcja do pobierania IP"""
    return request.client.host if request.client else None

@router.get("/occupancy", response_model=CurrentOccupancyResponse)
async def get_current_occupancy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera aktualne obłożenie wszystkich oddziałów
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Timestamp (czas ostatniego zapisu)
    - Obłożenie każdego oddziału:
      - Nazwa oddziału
      - Aktualne obłożenie (liczba pacjentów)
      - Pojemność (maksymalna liczba łóżek)
      - Procent obłożenia
      - Status (LOW/MEDIUM/HIGH/CRITICAL)
      - Liczba dostępnych łóżek
    - Całkowite obłożenie wszystkich oddziałów
    - Całkowita pojemność
    - Ogólny procent obłożenia
    
    **Statusy obłożenia:**
    - LOW: < 50% pojemności
    - MEDIUM: 50-70% pojemności
    - HIGH: 70-90% pojemności
    - CRITICAL: >= 90% pojemności
    """
    return DepartmentService.get_current_occupancy(db)

@router.post("/occupancy", response_model=DepartmentOccupancyResponse, status_code=201)
async def record_occupancy(
    occupancy_data: DepartmentOccupancyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Zapisuje nowe obłożenie oddziałów
    
    **Wymaga:** Bearer Token (tylko nurse, doctor, admin)
    
    **Parametry:**
    - timestamp: Czas pomiaru
    - sor: Obłożenie SOR (0-25)
    - interna: Obłożenie Interny (0-50)
    - kardiologia: Obłożenie Kardiologii (0-30)
    - chirurgia: Obłożenie Chirurgii (0-35)
    - ortopedia: Obłożenie Ortopedii (0-25)
    - neurologia: Obłożenie Neurologii (0-20)
    - pediatria: Obłożenie Pediatrii (0-30)
    - ginekologia: Obłożenie Ginekologii (0-20)
    
    **Zwraca:**
    - Zapisany rekord obłożenia
    
    **Uwaga:** Timestamp musi być unikalny. Nie można zapisać dwóch pomiarów dla tego samego czasu.
    """
    if current_user.role == 'receptionist':
        raise HTTPException(
            status_code=403,
            detail="Receptionist cannot record occupancy"
        )
    
    ip_address = get_ip_address(request)
    
    return DepartmentService.record_occupancy(
        db=db,
        occupancy_data=occupancy_data,
        user_id=current_user.id,
        ip_address=ip_address
    )

@router.get("/{department}/history", response_model=OccupancyHistory)
async def get_department_history(
    department: str,
    hours: int = Query(24, ge=1, le=168, description="Liczba godzin wstecz (1-168, czyli max 7 dni)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera historię obłożenia konkretnego oddziału
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - department: Nazwa oddziału (SOR, Interna, Kardiologia, Chirurgia, Ortopedia, Neurologia, Pediatria, Ginekologia)
    - hours: Liczba godzin wstecz (domyślnie 24, max 168)
    
    **Zwraca:**
    - Nazwa oddziału
    - Historia obłożenia (timestamp, occupancy, percentage)
    - Średnie obłożenie w okresie
    - Szczytowe obłożenie
    - Czas szczytu
    """
    return DepartmentService.get_occupancy_history(db, department, hours)

@router.get("/{department}/stats", response_model=DepartmentStats)
async def get_department_stats(
    department: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera statystyki konkretnego oddziału
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - department: Nazwa oddziału
    
    **Zwraca:**
    - Aktualne obłożenie
    - Pojemność
    - Procent obłożenia
    - Liczba pacjentów w ostatnich 24h
    - Średni czas pobytu (jeśli dostępny)
    - Godziny szczytu (na podstawie ostatnich 7 dni)
    """
    return DepartmentService.get_department_stats(db, department)

@router.get("/{department}/predict")
async def predict_occupancy(
    department: str,
    hours_ahead: int = Query(6, ge=1, le=24, description="Liczba godzin w przód (1-24)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Prognozuje obłożenie oddziału
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - department: Nazwa oddziału
    - hours_ahead: Liczba godzin w przód (domyślnie 6, max 24)
    
    **Zwraca:**
    - Lista prognoz dla każdej godziny
    - Każda prognoza zawiera:
      - Timestamp
      - Przewidywane obłożenie
      - Poziom pewności (confidence)
      - Uwagi
    
    **Uwaga:** To jest uproszczona wersja (moving average).
    Pełna implementacja wymaga modelu LSTM, który można trenować na danych z department_arrangement_data.csv
    """
    predictions = DepartmentService.predict_occupancy(db, department, hours_ahead)
    
    return {
        "department": department,
        "hours_ahead": hours_ahead,
        "predictions": predictions,
        "note": "This is a simplified prediction using moving average. For better accuracy, train an LSTM model on historical data."
    }

@router.get("/summary/all")
async def get_all_departments_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera podsumowanie wszystkich oddziałów
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Timestamp
    - Całkowite obłożenie
    - Całkowita pojemność
    - Ogólny procent obłożenia
    - Podsumowanie każdego oddziału:
      - Aktualne obłożenie
      - Pojemność
      - Procent
      - Status
      - Dostępne łóżka
    """
    return DepartmentService.get_all_departments_summary(db)

@router.get("/capacity/list")
async def get_departments_capacity(
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera pojemności wszystkich oddziałów
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Lista oddziałów z pojemnościami
    """
    from app.services.department_service import DEPARTMENT_CAPACITY
    
    return {
        "departments": [
            {"name": dept, "capacity": cap}
            for dept, cap in DEPARTMENT_CAPACITY.items()
        ]
    }

@router.get("/alerts/critical")
async def get_critical_departments(
    threshold: float = Query(0.9, ge=0.5, le=1.0, description="Próg obłożenia (domyślnie 0.9 = 90%)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera listę oddziałów z krytycznym obłożeniem
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - threshold: Próg obłożenia (domyślnie 0.9 = 90%)
    
    **Zwraca:**
    - Lista oddziałów przekraczających próg
    - Dla każdego oddziału:
      - Nazwa
      - Aktualne obłożenie
      - Pojemność
      - Procent
      - Status
    """
    current = DepartmentService.get_current_occupancy(db)
    
    critical_departments = [
        {
            "department": name,
            "current_occupancy": info.current_occupancy,
            "capacity": info.capacity,
            "percentage": info.occupancy_percentage,
            "status": info.status,
            "available_beds": info.available_beds
        }
        for name, info in current.departments.items()
        if info.occupancy_percentage >= (threshold * 100)
    ]
    
    return {
        "threshold_percentage": threshold * 100,
        "critical_count": len(critical_departments),
        "departments": critical_departments,
        "timestamp": current.timestamp
    }

@router.get("/recommendations/{department}")
async def get_department_recommendations(
    department: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera rekomendacje dla oddziału
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - department: Nazwa oddziału
    
    **Zwraca:**
    - Status oddziału
    - Rekomendacje działań
    - Alternatywne oddziały (jeśli przepełniony)
    """
    current = DepartmentService.get_current_occupancy(db)
    
    if department not in current.departments:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department. Available: {', '.join(current.departments.keys())}"
        )
    
    dept_info = current.departments[department]
    
    recommendations = []
    alternatives = []
    
    if dept_info.occupancy_percentage >= 90:
        recommendations.append("CRITICAL: Oddział przepełniony! Rozważ przekierowanie pacjentów.")
        recommendations.append("Zaalarmuj kierownika oddziału.")
        recommendations.append("Sprawdź możliwość wypisania stabilnych pacjentów.")
        
        # Znajdź alternatywy
        for alt_name, alt_info in current.departments.items():
            if alt_name != department and alt_info.occupancy_percentage < 70:
                alternatives.append({
                    "department": alt_name,
                    "available_beds": alt_info.available_beds,
                    "percentage": alt_info.occupancy_percentage
                })
    
    elif dept_info.occupancy_percentage >= 70:
        recommendations.append("HIGH: Wysoke obłożenie. Monitoruj sytuację.")
        recommendations.append("Przygotuj plan awaryjny.")
        
    elif dept_info.occupancy_percentage >= 50:
        recommendations.append("MEDIUM: Obłożenie normalne. Brak specjalnych działań.")
        
    else:
        recommendations.append("LOW: Niskie obłożenie. Oddział może przyjąć więcej pacjentów.")
    
    return {
        "department": department,
        "current_status": dept_info.status,
        "occupancy_percentage": dept_info.occupancy_percentage,
        "available_beds": dept_info.available_beds,
        "recommendations": recommendations,
        "alternative_departments": alternatives if alternatives else None
    }
