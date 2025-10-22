from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.models import DepartmentOccupancy, Patient, TriagePrediction
from app.schemas import (
    DepartmentOccupancyCreate,
    DepartmentOccupancyResponse,
    DepartmentInfo,
    CurrentOccupancyResponse,
    OccupancyHistory,
    DepartmentStats
)
from app.services.audit_service import log_action

DEPARTMENT_CAPACITY = {
    "SOR": 25,
    "Interna": 50,
    "Kardiologia": 30,
    "Chirurgia": 35,
    "Ortopedia": 25,
    "Neurologia": 20,
    "Pediatria": 30,
    "Ginekologia": 20
}

class DepartmentService:
    """Service do zarządzania obłożeniem oddziałów"""
    
    @staticmethod
    def record_occupancy(
        db: Session,
        occupancy_data: DepartmentOccupancyCreate,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> DepartmentOccupancy:
        """
        Zapisuje obłożenie oddziałów
        
        Args:
            db: Sesja bazy danych
            occupancy_data: Dane obłożenia
            user_id: ID użytkownika (opcjonalne)
            ip_address: Adres IP
            
        Returns:
            Zapisane obłożenie
            
        Raises:
            HTTPException: Jeśli timestamp już istnieje
        """
        existing = db.query(DepartmentOccupancy).filter(
            DepartmentOccupancy.timestamp == occupancy_data.timestamp
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Occupancy record for this timestamp already exists"
            )
        
        occupancy = DepartmentOccupancy(**occupancy_data.model_dump())
        
        db.add(occupancy)
        db.commit()
        db.refresh(occupancy)
        
        if user_id:
            log_action(
                db=db,
                user_id=user_id,
                action="RECORD_OCCUPANCY",
                table_name="department_occupancy",
                record_id=occupancy.id,
                new_values=occupancy_data.model_dump(),
                ip_address=ip_address
            )
        
        return occupancy
    
    @staticmethod
    def get_current_occupancy(db: Session) -> CurrentOccupancyResponse:
        """
        Pobiera aktualne obłożenie oddziałów
        
        Args:
            db: Sesja bazy danych
            
        Returns:
            Aktualne obłożenie wszystkich oddziałów
        """
        latest = db.query(DepartmentOccupancy).order_by(
            DepartmentOccupancy.timestamp.desc()
        ).first()
        
        if not latest:
            latest = DepartmentOccupancy(
                timestamp=datetime.now(),
                sor=0, interna=0, kardiologia=0, chirurgia=0,
                ortopedia=0, neurologia=0, pediatria=0, ginekologia=0
            )
        
        departments = {}
        total_occupancy = 0
        total_capacity = 0
        
        for dept_name, capacity in DEPARTMENT_CAPACITY.items():
            dept_key = dept_name.lower()
            current_occ = getattr(latest, dept_key, 0) or 0
            
            percentage = (current_occ / capacity * 100) if capacity > 0 else 0
            
            if percentage >= 90:
                status_text = "CRITICAL"
            elif percentage >= 70:
                status_text = "HIGH"
            elif percentage >= 50:
                status_text = "MEDIUM"
            else:
                status_text = "LOW"
            
            departments[dept_name] = DepartmentInfo(
                name=dept_name,
                current_occupancy=current_occ,
                capacity=capacity,
                occupancy_percentage=round(percentage, 2),
                status=status_text,
                available_beds=capacity - current_occ
            )
            
            total_occupancy += current_occ
            total_capacity += capacity
        
        overall_percentage = (total_occupancy / total_capacity * 100) if total_capacity > 0 else 0
        
        return CurrentOccupancyResponse(
            timestamp=latest.timestamp,
            departments=departments,
            total_occupancy=total_occupancy,
            total_capacity=total_capacity,
            overall_percentage=round(overall_percentage, 2)
        )
    
    @staticmethod
    def get_occupancy_history(
        db: Session,
        department: str,
        hours: int = 24
    ) -> OccupancyHistory:
        """
        Pobiera historię obłożenia oddziału
        
        Args:
            db: Sesja bazy danych
            department: Nazwa oddziału
            hours: Liczba godzin wstecz
            
        Returns:
            Historia obłożenia
            
        Raises:
            HTTPException: Jeśli oddział nie istnieje
        """
        if department not in DEPARTMENT_CAPACITY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid department. Must be one of: {', '.join(DEPARTMENT_CAPACITY.keys())}"
            )
        
        date_from = datetime.now() - timedelta(hours=hours)
        
        records = db.query(DepartmentOccupancy).filter(
            DepartmentOccupancy.timestamp >= date_from
        ).order_by(
            DepartmentOccupancy.timestamp.asc()
        ).all()
        
        dept_key = department.lower()
        capacity = DEPARTMENT_CAPACITY[department]
        
        history = []
        occupancies = []
        
        for record in records:
            occ = getattr(record, dept_key, 0) or 0
            percentage = (occ / capacity * 100) if capacity > 0 else 0
            
            history.append({
                "timestamp": record.timestamp.isoformat(),
                "occupancy": occ,
                "percentage": round(percentage, 2)
            })
            
            occupancies.append(occ)
        
        avg_occ = sum(occupancies) / len(occupancies) if occupancies else 0
        peak_occ = max(occupancies) if occupancies else 0
        peak_idx = occupancies.index(peak_occ) if occupancies else 0
        peak_time = records[peak_idx].timestamp if records else datetime.now()
        
        return OccupancyHistory(
            department=department,
            history=history,
            average_occupancy=round(avg_occ, 2),
            peak_occupancy=peak_occ,
            peak_timestamp=peak_time
        )
    
    @staticmethod
    def get_department_stats(db: Session, department: str) -> DepartmentStats:
        """
        Pobiera statystyki oddziału
        
        Args:
            db: Sesja bazy danych
            department: Nazwa oddziału
            
        Returns:
            Statystyki oddziału
            
        Raises:
            HTTPException: Jeśli oddział nie istnieje
        """
        if department not in DEPARTMENT_CAPACITY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid department. Must be one of: {', '.join(DEPARTMENT_CAPACITY.keys())}"
            )
        
        from sqlalchemy import func, extract
        
        latest = db.query(DepartmentOccupancy).order_by(
            DepartmentOccupancy.timestamp.desc()
        ).first()
        
        dept_key = department.lower()
        current_occ = getattr(latest, dept_key, 0) if latest else 0
        capacity = DEPARTMENT_CAPACITY[department]
        percentage = (current_occ / capacity * 100) if capacity > 0 else 0
        
        date_24h_ago = datetime.now() - timedelta(hours=24)
        
        patients_24h = db.query(func.count(Patient.id)).join(
            TriagePrediction
        ).filter(
            TriagePrediction.przypisany_oddzial == department,
            Patient.data_przyjecia >= date_24h_ago
        ).scalar() or 0
        
        date_7d_ago = datetime.now() - timedelta(days=7)
        
        peak_hours_data = db.query(
            extract('hour', DepartmentOccupancy.timestamp).label('hour'),
            func.avg(getattr(DepartmentOccupancy, dept_key)).label('avg_occ')
        ).filter(
            DepartmentOccupancy.timestamp >= date_7d_ago
        ).group_by(
            extract('hour', DepartmentOccupancy.timestamp)
        ).order_by(
            func.avg(getattr(DepartmentOccupancy, dept_key)).desc()
        ).limit(3).all()
        
        peak_hours = [int(hour) for hour, _ in peak_hours_data]
        
        return DepartmentStats(
            department=department,
            current_occupancy=current_occ,
            capacity=capacity,
            occupancy_percentage=round(percentage, 2),
            patients_last_24h=patients_24h,
            avg_stay_duration_hours=None,  # TODO: Implementacja gdy będą dane o czasie pobytu
            peak_hours=peak_hours
        )
    
    @staticmethod
    def predict_occupancy(
        db: Session,
        department: str,
        hours_ahead: int = 6
    ) -> List[Dict]:
        """
        Prognozuje obłożenie oddziału (uproszczona wersja)
        
        Args:
            db: Sesja bazy danych
            department: Nazwa oddziału
            hours_ahead: Ile godzin w przód prognozować
            
        Returns:
            Lista prognoz
            
        Note:
            To jest uproszczona wersja. Pełna implementacja wymagałaby modelu LSTM.
        """
        if department not in DEPARTMENT_CAPACITY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid department. Must be one of: {', '.join(DEPARTMENT_CAPACITY.keys())}"
            )
        
        date_from = datetime.now() - timedelta(hours=24)
        
        records = db.query(DepartmentOccupancy).filter(
            DepartmentOccupancy.timestamp >= date_from
        ).order_by(
            DepartmentOccupancy.timestamp.desc()
        ).all()
        
        if not records:
            return []
        
        dept_key = department.lower()
        
        recent_values = [getattr(r, dept_key, 0) or 0 for r in records[:6]]
        avg = sum(recent_values) / len(recent_values) if recent_values else 0
        
        predictions = []
        for i in range(1, hours_ahead + 1):
            future_time = datetime.now() + timedelta(hours=i)
            predictions.append({
                "timestamp": future_time.isoformat(),
                "predicted_occupancy": int(avg),
                "confidence": "low",  # Niska pewność dla uproszczonego modelu
                "note": "Simple moving average prediction"
            })
        
        return predictions
    
    @staticmethod
    def get_all_departments_summary(db: Session) -> Dict:
        """
        Pobiera podsumowanie wszystkich oddziałów
        
        Args:
            db: Sesja bazy danych
            
        Returns:
            Podsumowanie wszystkich oddziałów
        """
        current = DepartmentService.get_current_occupancy(db)
        
        summary = {
            "timestamp": current.timestamp.isoformat(),
            "total_occupancy": current.total_occupancy,
            "total_capacity": current.total_capacity,
            "overall_percentage": current.overall_percentage,
            "departments": {}
        }
        
        for dept_name, info in current.departments.items():
            summary["departments"][dept_name] = {
                "current_occupancy": info.current_occupancy,
                "capacity": info.capacity,
                "percentage": info.occupancy_percentage,
                "status": info.status,
                "available_beds": info.available_beds
            }
        
        return summary
