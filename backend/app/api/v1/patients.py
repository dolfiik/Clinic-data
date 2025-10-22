from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db, get_current_active_user
from app.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListItem,
    PatientWithPrediction,
    PatientWithDetails,
    PaginatedResponse,
    MessageResponse
)
from app.services import PatientService
from app.models import User

router = APIRouter()

def get_ip_address(request: Request) -> str:
    """Pomocnicza funkcja do pobierania IP"""
    return request.client.host if request.client else None

@router.get("/", response_model=PaginatedResponse[PatientListItem])
async def get_patients(
    page: int = Query(1, ge=1, description="Numer strony"),
    size: int = Query(20, ge=1, le=100, description="Rozmiar strony"),
    status: Optional[str] = Query(None, description="Filtr po statusie (oczekujący, w_leczeniu, wypisany, przekazany)"),
    triage_category: Optional[int] = Query(None, ge=1, le=5, description="Filtr po kategorii triaży (1-5)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera listę pacjentów z paginacją i filtrami
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - page: Numer strony (domyślnie 1)
    - size: Liczba rekordów na stronę (1-100, domyślnie 20)
    - status: Opcjonalny filtr po statusie
    - triage_category: Opcjonalny filtr po kategorii triaży
    
    **Zwraca:**
    - Lista pacjentów z informacjami o paginacji
    """
    return PatientService.list_patients(
        db=db,
        page=page,
        size=size,
        status=status,
        triage_category=triage_category
    )

@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Tworzy nowego pacjenta
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - Wszystkie wymagane dane pacjenta (wiek, płeć, parametry vitalne)
    
    **Zwraca:**
    - Utworzony pacjent ze statusem 'oczekujący'
    
    **Uwaga:** Po utworzeniu należy wykonać predykcję triaży przez POST /triage/predict
    """
    ip_address = get_ip_address(request)
    
    patient = PatientService.create_patient(
        db=db,
        patient_data=patient_data,
        user_id=current_user.id,
        ip_address=ip_address
    )
    
    return PatientResponse.model_validate(patient)

@router.get("/{patient_id}", response_model=PatientWithPrediction)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera dane pacjenta z predykcją triaży
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - patient_id: ID pacjenta
    
    **Zwraca:**
    - Dane pacjenta wraz z predykcją (jeśli została wykonana)
    """
    patient = PatientService.get_patient(db, patient_id)
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
    
    return patient

@router.get("/{patient_id}/details", response_model=PatientWithDetails)
async def get_patient_details(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera pełne szczegóły pacjenta
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - patient_id: ID pacjenta
    
    **Zwraca:**
    - Pełne dane pacjenta z predykcją i informacjami o użytkowniku, który go wprowadził
    """
    patient = PatientService.get_patient_details(db, patient_id)
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
    
    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    updates: PatientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Aktualizuje dane pacjenta
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - patient_id: ID pacjenta
    - updates: Pola do zaktualizowania (wszystkie opcjonalne)
    
    **Zwraca:**
    - Zaktualizowany pacjent
    """
    ip_address = get_ip_address(request)
    
    patient = PatientService.update_patient(
        db=db,
        patient_id=patient_id,
        updates=updates,
        user_id=current_user.id,
        ip_address=ip_address
    )
    
    return PatientResponse.model_validate(patient)

@router.delete("/{patient_id}", response_model=MessageResponse)
async def delete_patient(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Usuwa pacjenta
    
    **Wymaga:** Bearer Token (tylko admin lub doctor)
    
    **Parametry:**
    - patient_id: ID pacjenta
    
    **Zwraca:**
    - Potwierdzenie usunięcia
    """
    if current_user.role not in ['admin', 'doctor']:
        raise HTTPException(
            status_code=403,
            detail="Only admin or doctor can delete patients"
        )
    
    ip_address = get_ip_address(request)
    
    PatientService.delete_patient(
        db=db,
        patient_id=patient_id,
        user_id=current_user.id,
        ip_address=ip_address
    )
    
    return MessageResponse(
        message=f"Patient {patient_id} successfully deleted",
        success=True
    )

@router.patch("/{patient_id}/status", response_model=PatientResponse)
async def change_patient_status(
    patient_id: int,
    new_status: str = Query(..., description="Nowy status: oczekujący, w_leczeniu, wypisany, przekazany"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Zmienia status pacjenta
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - patient_id: ID pacjenta
    - new_status: Nowy status (oczekujący, w_leczeniu, wypisany, przekazany)
    
    **Zwraca:**
    - Zaktualizowany pacjent
    """
    ip_address = get_ip_address(request)
    
    patient = PatientService.change_patient_status(
        db=db,
        patient_id=patient_id,
        new_status=new_status,
        user_id=current_user.id,
        ip_address=ip_address
    )
    
    return PatientResponse.model_validate(patient)

@router.get("/waiting/list", response_model=list[PatientWithPrediction])
async def get_waiting_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera listę oczekujących pacjentów
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Lista oczekujących pacjentów posortowana według:
      1. Kategorii triaży (1 = najwyższy priorytet)
      2. Czasu przyjęcia (starsi pacjenci pierwsi)
    """
    return PatientService.get_waiting_patients(db)

@router.get("/search/query", response_model=list[PatientListItem])
async def search_patients(
    q: str = Query(..., min_length=1, description="Zapytanie wyszukiwania"),
    limit: int = Query(20, ge=1, le=100, description="Limit wyników"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Wyszukuje pacjentów
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - q: Tekst do wyszukania (ID, szablon przypadku)
    - limit: Maksymalna liczba wyników (domyślnie 20)
    
    **Zwraca:**
    - Lista znalezionych pacjentów
    """
    return PatientService.search_patients(db, q, limit)
