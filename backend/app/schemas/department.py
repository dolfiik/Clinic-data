from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from datetime import datetime

class DepartmentOccupancyBase(BaseModel):
    """Bazowe dane obłożenia oddziałów"""
    sor: int = Field(default=0, ge=0)
    interna: int = Field(default=0, ge=0)
    kardiologia: int = Field(default=0, ge=0)
    chirurgia: int = Field(default=0, ge=0)
    ortopedia: int = Field(default=0, ge=0)
    neurologia: int = Field(default=0, ge=0)
    pediatria: int = Field(default=0, ge=0)
    ginekologia: int = Field(default=0, ge=0)

class DepartmentOccupancyCreate(DepartmentOccupancyBase):
    """Schema do tworzenia wpisu obłożenia"""
    timestamp: datetime

class DepartmentOccupancyResponse(DepartmentOccupancyBase):
    """Schema odpowiedzi z obłożeniem"""
    id: int
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class DepartmentInfo(BaseModel):
    """Informacje o pojedynczym oddziale"""
    name: str
    current_occupancy: int
    capacity: int
    occupancy_percentage: float
    status: str  # LOW, MEDIUM, HIGH, CRITICAL
    available_beds: int

class CurrentOccupancyResponse(BaseModel):
    """Aktualne obłożenie wszystkich oddziałów"""
    timestamp: datetime
    departments: Dict[str, DepartmentInfo]
    total_occupancy: int
    total_capacity: int
    overall_percentage: float

class DepartmentCapacity(BaseModel):
    """Pojemność oddziału"""
    department: str
    capacity: int

class OccupancyHistory(BaseModel):
    """Historia obłożenia oddziału"""
    department: str
    history: list[Dict[str, Any]]  # [{timestamp, occupancy, percentage}, ...]
    average_occupancy: float
    peak_occupancy: int
    peak_timestamp: datetime

class DepartmentStats(BaseModel):
    """Statystyki oddziału"""
    department: str
    current_occupancy: int
    capacity: int
    occupancy_percentage: float
    patients_last_24h: int
    avg_stay_duration_hours: Optional[float]
    peak_hours: list[int]  
