from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal

class TriagePredictionBase(BaseModel):
    """Bazowe pola predykcji"""
    kategoria_triazu: int = Field(..., ge=1, le=5, description="Kategoria triaży (1-5)")
    przypisany_oddzial: str = Field(..., description="Przypisany oddział")
    oddzial_docelowy: Optional[str] = Field(None, description="Docelowy oddział")

class TriagePredictionCreate(TriagePredictionBase):
    """Schema do tworzenia predykcji"""
    patient_id: int
    prob_kat_1: Decimal = Field(..., ge=0, le=1)
    prob_kat_2: Decimal = Field(..., ge=0, le=1)
    prob_kat_3: Decimal = Field(..., ge=0, le=1)
    prob_kat_4: Decimal = Field(..., ge=0, le=1)
    prob_kat_5: Decimal = Field(..., ge=0, le=1)
    model_version: str
    confidence_score: Decimal = Field(..., ge=0, le=1)

class TriagePredictionResponse(TriagePredictionBase):
    """Schema odpowiedzi predykcji"""
    id: int
    patient_id: int
    probabilities: Dict[str, float] = Field(..., description="Prawdopodobieństwa dla każdej kategorii")
    model_version: str
    confidence_score: float
    predicted_at: datetime
    
    class Config:
        from_attributes = True

class TriagePredictRequest(BaseModel):
    """Request do wykonania predykcji dla istniejącego pacjenta"""
    patient_id: int

class TriagePredictResponse(BaseModel):
    """Odpowiedź z predykcją"""
    patient_id: int
    kategoria_triazu: int
    probabilities: Dict[str, float]
    przypisany_oddzial: str
    confidence_score: float
    model_version: str

class TriageStatsResponse(BaseModel):
    """Statystyki triaży"""
    total_patients: int
    by_category: Dict[str, int] = Field(..., description="Liczba pacjentów w każdej kategorii")
    by_department: Dict[str, int] = Field(..., description="Liczba pacjentów na każdym oddziale")
    average_confidence: float
    last_updated: datetime

class DailyTriageStats(BaseModel):
    """Dzienne statystyki triaży"""
    data: datetime
    liczba_pacjentow: int
    kat_1_natychmiastowy: int
    kat_2_pilny: int
    kat_3_stabilny: int
    kat_4_niski: int
    kat_5_bardzo_niski: int
    avg_czas_do_triazu_min: Optional[float]
    avg_confidence: Optional[float]

class CategoryDistribution(BaseModel):
    """Rozkład kategorii triaży"""
    category: int
    count: int
    percentage: float
    label: str

class TriageAnalytics(BaseModel):
    """Zaawansowana analityka triaży"""
    total_predictions: int
    category_distribution: list[CategoryDistribution]
    average_confidence: float
    model_version: str
    period_start: datetime
    period_end: datetime
