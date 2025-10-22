from typing import Optional
from datetime import datetime
from decimal import Decimal

class PatientBase(BaseModel):
    """Bazowe pola pacjenta"""
    wiek: int = Field(..., ge=0, le=120, description="Wiek pacjenta (0-120)")
    plec: str = Field(..., pattern="^[MK]$", description="Płeć: M lub K")
    tetno: Optional[Decimal] = Field(None, ge=0, le=300, description="Tętno (0-300)")
    cisnienie_skurczowe: Optional[Decimal] = Field(None, ge=0, le=300, description="Ciśnienie skurczowe (0-300)")
    cisnienie_rozkurczowe: Optional[Decimal] = Field(None, ge=0, le=200, description="Ciśnienie rozkurczowe (0-200)")
    temperatura: Optional[Decimal] = Field(None, ge=30, le=45, description="Temperatura (30-45°C)")
    saturacja: Optional[Decimal] = Field(None, ge=0, le=100, description="Saturacja (0-100%)")
    gcs: Optional[int] = Field(None, ge=3, le=15, description="Glasgow Coma Scale (3-15)")
    bol: Optional[int] = Field(None, ge=0, le=10, description="Skala bólu (0-10)")
    czestotliwosc_oddechow: Optional[Decimal] = Field(None, ge=0, le=100, description="Częstotliwość oddechów (0-100)")
    czas_od_objawow_h: Optional[Decimal] = Field(None, ge=0, description="Czas od objawów w godzinach")
    szablon_przypadku: Optional[str] = Field(None, max_length=100, description="Szablon przypadku medycznego")
    notatki: Optional[str] = Field(None, description="Dodatkowe notatki")

class PatientCreate(PatientBase):
    """Schema do tworzenia nowego pacjenta"""
    pass

class PatientUpdate(BaseModel):
    """Schema do aktualizacji pacjenta - wszystkie pola opcjonalne"""
    wiek: Optional[int] = Field(None, ge=0, le=120)
    plec: Optional[str] = Field(None, pattern="^[MK]$")
    tetno: Optional[Decimal] = Field(None, ge=0, le=300)
    cisnienie_skurczowe: Optional[Decimal] = Field(None, ge=0, le=300)
    cisnienie_rozkurczowe: Optional[Decimal] = Field(None, ge=0, le=200)
    temperatura: Optional[Decimal] = Field(None, ge=30, le=45)
    saturacja: Optional[Decimal] = Field(None, ge=0, le=100)
    gcs: Optional[int] = Field(None, ge=3, le=15)
    bol: Optional[int] = Field(None, ge=0, le=10)
    czestotliwosc_oddechow: Optional[Decimal] = Field(None, ge=0, le=100)
    czas_od_objawow_h: Optional[Decimal] = Field(None, ge=0)
    szablon_przypadku: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(oczekujący|w_leczeniu|wypisany|przekazany)$")
    notatki: Optional[str] = None

class PatientResponse(PatientBase):
    """Schema odpowiedzi z danymi pacjenta"""
    id: int
    data_przyjecia: datetime
    wprowadzony_przez: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PatientListItem(BaseModel):
    """Skrócona wersja dla list pacjentów"""
    id: int
    wiek: int
    plec: str
    status: str
    data_przyjecia: datetime
    szablon_przypadku: Optional[str]
    
    class Config:
        from_attributes = True

class PatientWithPrediction(PatientResponse):
    """Pacjent z predykcją triaży"""
    prediction: Optional["TriagePredictionResponse"] = None
    
    class Config:
        from_attributes = True

class PatientWithDetails(PatientResponse):
    """Pacjent z pełnymi szczegółami"""
    prediction: Optional["TriagePredictionResponse"] = None
    wprowadzony_przez_username: Optional[str] = None
    wprowadzony_przez_email: Optional[str] = None
    
    class Config:
        from_attributes = True

