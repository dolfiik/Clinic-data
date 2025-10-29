from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.api.deps import get_db, get_current_active_user
from app.schemas import (
    TriagePredictRequest,
    TriagePredictResponse,
    TriagePredictionResponse,
    TriageStatsResponse,
    DailyTriageStats,
    TriageAnalytics
)
from app.services import TriageService
from app.ml.predictor import predictor
from app.models import User
from typing import List, Dict

router = APIRouter()

def get_ip_address(request: Request) -> str:
    """Pomocnicza funkcja do pobierania IP"""
    return request.client.host if request.client else None

@router.post("/predict", response_model=TriagePredictResponse, status_code=201)
async def predict_triage(
    prediction_request: TriagePredictRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Wykonuje predykcję kategorii triaży dla pacjenta
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - patient_id: ID pacjenta (musi istnieć w bazie)
    
    **Zwraca:**
    - Kategoria triaży (1-5)
    - Prawdopodobieństwa dla każdej kategorii
    - Przypisany oddział
    - Pewność predykcji (confidence score)
    - Wersja modelu ML
    
    **Proces:**
    1. Pobiera dane pacjenta z bazy
    2. Przekazuje do modelu ML (Random Forest)
    3. Określa przypisany oddział na podstawie kategorii i szablonu
    4. Zapisuje predykcję w bazie
    5. Loguje akcję w audit log
    
    **Kategorie triaży:**
    - 1: Natychmiastowy (Resuscytacja - zagrożenie życia)
    - 2: Pilny (Bardzo pilny - ciężki stan)
    - 3: Stabilny (Pilny - stabilny pacjent)
    - 4: Niski priorytet (Mniej pilny)
    - 5: Bardzo niski (Nieistotny)
    """
    ip_address = get_ip_address(request)
    
    return TriageService.predict_triage(
        db=db,
        patient_id=prediction_request.patient_id,
        user_id=current_user.id,
        ip_address=ip_address
    )

@router.get("/prediction/{patient_id}", response_model=TriagePredictionResponse)
async def get_prediction(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera predykcję triaży dla pacjenta
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - patient_id: ID pacjenta
    
    **Zwraca:**
    - Predykcja triaży (jeśli została wykonana)
    """
    prediction = TriageService.get_prediction(db, patient_id)
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail="No triage prediction found for this patient"
        )
    
    return prediction

@router.get("/stats", response_model=TriageStatsResponse)
async def get_triage_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera ogólne statystyki triaży
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Całkowita liczba pacjentów
    - Liczba pacjentów w każdej kategorii (1-5)
    - Liczba pacjentów na każdym oddziale
    - Średnia pewność predykcji (confidence)
    - Czas ostatniej aktualizacji
    """
    return TriageService.get_stats(db)

@router.get("/daily-stats", response_model=list[DailyTriageStats])
async def get_daily_stats(
    days: int = Query(7, ge=1, le=90, description="Liczba dni wstecz (1-90)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera dzienne statystyki triaży
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - days: Liczba dni wstecz (domyślnie 7, max 90)
    
    **Zwraca:**
    - Lista dziennych statystyk zawierająca:
      - Datę
      - Liczbę pacjentów
      - Rozkład po kategoriach (1-5)
      - Średni czas do wykonania triaży
      - Średnią pewność predykcji
    """
    return TriageService.get_daily_stats(db, days)

@router.get("/analytics", response_model=TriageAnalytics)
async def get_analytics(
    date_from: Optional[datetime] = Query(None, description="Data początkowa (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Data końcowa (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera zaawansowaną analitykę triaży
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - date_from: Opcjonalna data początkowa (domyślnie 30 dni wstecz)
    - date_to: Opcjonalna data końcowa (domyślnie teraz)
    
    **Zwraca:**
    - Całkowita liczba predykcji
    - Szczegółowy rozkład kategorii z procentami
    - Średnia pewność predykcji
    - Wersja modelu
    - Okres analizy
    """
    return TriageService.get_analytics(db, date_from, date_to)

@router.get("/model-info")
async def get_model_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera informacje o modelu ML
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Stan modelu (załadowany/nie załadowany)
    - Wersja modelu
    - Typ modelu (np. RandomForestClassifier)
    - Parametry modelu (n_estimators, max_depth, etc.)
    - Liczba cech (features)
    - Informacje o preprocessorze
    """
    return predictor.get_model_info()

@router.get("/feature-importance")
async def get_feature_importance(
    top_n: int = Query(20, ge=1, le=50, description="Liczba najważniejszych cech do zwrócenia"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera ważność cech (feature importance)
    
    **Wymaga:** Bearer Token
    
    **Parametry:**
    - top_n: Liczba najważniejszych cech (domyślnie 20, max 50)
    
    **Zwraca:**
    - Słownik {feature_name: importance_score}
    - Posortowany od najważniejszej cechy
    
    **Uwaga:** Działa tylko dla modeli tree-based (Random Forest, Gradient Boosting)
    """
    importance = predictor.get_feature_importance(top_n=top_n)
    
    if not importance:
        raise HTTPException(
            status_code=400,
            detail="Feature importance not available for this model type"
        )
    
    return {
        "features": importance,
        "model_type": type(predictor.model).__name__ if predictor.model else "unknown"
    }

@router.post("/reload-model")
async def reload_model(
    current_user: User = Depends(get_current_active_user)
):
    """
    Przeładowuje model ML (po aktualizacji)
    
    **Wymaga:** Bearer Token (tylko admin)
    
    **Zwraca:**
    - Potwierdzenie przeładowania
    - Nową wersję modelu
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Only admin can reload the model"
        )
    
    predictor.reload_model()
    
    return {
        "message": "Model reloaded successfully",
        "model_version": predictor.model_version,
        "model_info": predictor.get_model_info()
    }

@router.get("/categories/info")
async def get_categories_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Pobiera informacje o kategoriach triaży
    
    **Wymaga:** Bearer Token
    
    **Zwraca:**
    - Opis każdej kategorii (1-5)
    - Typowe czasy oczekiwania
    - Przykładowe przypadki
    """
    return {
        "categories": [
            {
                "category": 1,
                "name": "Natychmiastowy",
                "color": "red",
                "description": "Resuscytacja - natychmiastowe zagrożenie życia",
                "max_wait_time_minutes": 0,
                "examples": ["Zawał STEMI", "Udar ciężki", "Uraz wielonarządowy"]
            },
            {
                "category": 2,
                "name": "Pilny",
                "color": "orange",
                "description": "Bardzo pilny - ciężki stan wymagający szybkiej interwencji",
                "max_wait_time_minutes": 10,
                "examples": ["Zapalenie płuc ciężkie", "Zapalenie wyrostka", "Silne krwawienie"]
            },
            {
                "category": 3,
                "name": "Stabilny",
                "color": "yellow",
                "description": "Pilny - stabilny pacjent wymagający leczenia",
                "max_wait_time_minutes": 30,
                "examples": ["Złamanie proste", "Infekcja moczu", "Zaostrzenie astmy"]
            },
            {
                "category": 4,
                "name": "Niski priorytet",
                "color": "green",
                "description": "Mniej pilny - niskie ryzyko, może poczekać",
                "max_wait_time_minutes": 60,
                "examples": ["Ból brzucha łagodny", "Skręcenie lekkie", "Migrena"]
            },
            {
                "category": 5,
                "name": "Bardzo niski",
                "color": "blue",
                "description": "Nieistotny - brak ryzyka, planowa wizyta",
                "max_wait_time_minutes": 120,
                "examples": ["Przeziębienie", "Kontrola", "Receptura"]
            }
        ]
    }

@router.get("/templates", response_model=List[Dict[str, str]])
async def get_available_templates():
    """Zwraca listę dostępnych szablonów przypadków medycznych"""
    from app.ml.preprocessor import preprocessor
    
    template_labels = {
        'ból_brzucha_łagodny': 'Ból brzucha (łagodny)',
        'infekcja_moczu': 'Infekcja układu moczowego',
        'kontrola': 'Kontrola / Badanie kontrolne',
        'migrena': 'Migrena / Ból głowy',
        'przeziębienie': 'Przeziębienie / Infekcja górnych dróg oddechowych',
        'receptura': 'Wypisanie recepty / Przedłużenie leczenia',
        'silne_krwawienie': 'Silne krwawienie',
        'skręcenie_lekkie': 'Skręcenie / Zwichnięcie (lekkie)',
        'udar_ciężki': 'Udar mózgu (ciężki)',
        'uraz_wielonarządowy': 'Uraz wielonarządowy / Wypadek',
        'zaostrzenie_astmy': 'Zaostrzenie astmy / Duszność',
        'zapalenie_płuc_ciężkie': 'Zapalenie płuc (ciężkie)',
        'zapalenie_wyrostka': 'Zapalenie wyrostka robaczkowego',
        'zawał_STEMI': 'Zawał serca (STEMI) / Ból w klatce piersiowej',
        'złamanie_proste': 'Złamanie kości (proste)'
    }
    
    templates = []
    for template_value in preprocessor.templates:
        templates.append({
            "value": template_value,
            "label": template_labels.get(template_value, template_value)
        })
    
    return templates
