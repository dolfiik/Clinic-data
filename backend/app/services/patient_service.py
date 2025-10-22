from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status

from app.models import Patient, User, TriagePrediction
from app.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListItem,
    PatientWithPrediction,
    PatientWithDetails,
    PaginatedResponse
)
from app.services.audit_service import log_action

class PatientService:
    """Service do zarządzania pacjentami"""
    
    @staticmethod
    def create_patient(
        db: Session,
        patient_data: PatientCreate,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> Patient:
        """
        Tworzy nowego pacjenta
        
        Args:
            db: Sesja bazy danych
            patient_data: Dane pacjenta
            user_id: ID użytkownika tworzącego
            ip_address: Adres IP
            
        Returns:
            Utworzony pacjent
        """
        patient = Patient(
            **patient_data.model_dump(),
            wprowadzony_przez=user_id,
            status='oczekujący'
        )
        
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        log_action(
            db=db,
            user_id=user_id,
            action="CREATE_PATIENT",
            table_name="patients",
            record_id=patient.id,
            new_values=patient_data.model_dump(),
            ip_address=ip_address
        )
        
        return patient
    
    @staticmethod
    def get_patient(db: Session, patient_id: int) -> Optional[PatientWithPrediction]:
        """
        Pobiera pacjenta z predykcją
        
        Args:
            db: Sesja bazy danych
            patient_id: ID pacjenta
            
        Returns:
            Pacjent z predykcją lub None
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            return None
        
        return PatientWithPrediction.model_validate(patient)
    
    @staticmethod
    def get_patient_details(db: Session, patient_id: int) -> Optional[PatientWithDetails]:
        """
        Pobiera pacjenta z pełnymi szczegółami
        
        Args:
            db: Sesja bazy danych
            patient_id: ID pacjenta
            
        Returns:
            Pacjent z pełnymi szczegółami lub None
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            return None
        
        patient_dict = patient.to_dict()
        if patient.entered_by_user:
            patient_dict['wprowadzony_przez_username'] = patient.entered_by_user.username
            patient_dict['wprowadzony_przez_email'] = patient.entered_by_user.email
        
        if patient.prediction:
            patient_dict['prediction'] = patient.prediction.to_dict()
        
        return PatientWithDetails(**patient_dict)
    
    @staticmethod
    def list_patients(
        db: Session,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        triage_category: Optional[int] = None
    ) -> PaginatedResponse[PatientListItem]:
        """
        Lista pacjentów z paginacją i filtrami
        
        Args:
            db: Sesja bazy danych
            page: Numer strony
            size: Rozmiar strony
            status: Filtr po statusie
            triage_category: Filtr po kategorii triaży
            
        Returns:
            Paginowana lista pacjentów
        """
        query = db.query(Patient)
        
        if status:
            query = query.filter(Patient.status == status)
        
        if triage_category:
            query = query.join(TriagePrediction).filter(
                TriagePrediction.kategoria_triazu == triage_category
            )
        
        query = query.order_by(Patient.data_przyjecia.desc())
        
        total = query.count()
        
        offset = (page - 1) * size
        patients = query.offset(offset).limit(size).all()
        
        items = [PatientListItem.model_validate(p) for p in patients]
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    
    @staticmethod
    def update_patient(
        db: Session,
        patient_id: int,
        updates: PatientUpdate,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> Patient:
        """
        Aktualizuje pacjenta
        
        Args:
            db: Sesja bazy danych
            patient_id: ID pacjenta
            updates: Aktualizacje
            user_id: ID użytkownika aktualizującego
            ip_address: Adres IP
            
        Returns:
            Zaktualizowany pacjent
            
        Raises:
            HTTPException: Jeśli pacjent nie istnieje
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        old_values = patient.to_dict()
        
        update_data = updates.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(patient, field, value)
        
        db.commit()
        db.refresh(patient)
        
        log_action(
            db=db,
            user_id=user_id,
            action="UPDATE_PATIENT",
            table_name="patients",
            record_id=patient_id,
            old_values={k: old_values[k] for k in update_data.keys()},
            new_values=update_data,
            ip_address=ip_address
        )
        
        return patient
    
    @staticmethod
    def delete_patient(
        db: Session,
        patient_id: int,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Usuwa pacjenta
        
        Args:
            db: Sesja bazy danych
            patient_id: ID pacjenta
            user_id: ID użytkownika usuwającego
            ip_address: Adres IP
            
        Raises:
            HTTPException: Jeśli pacjent nie istnieje
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        patient_data = patient.to_dict()
        
        db.delete(patient)
        db.commit()
        
        log_action(
            db=db,
            user_id=user_id,
            action="DELETE_PATIENT",
            table_name="patients",
            record_id=patient_id,
            old_values=patient_data,
            ip_address=ip_address
        )
    
    @staticmethod
    def get_waiting_patients(db: Session) -> List[PatientWithPrediction]:
        """
        Pobiera listę oczekujących pacjentów
        
        Args:
            db: Sesja bazy danych
            
        Returns:
            Lista oczekujących pacjentów sortowana po kategorii triaży
        """
        patients = db.query(Patient).join(
            TriagePrediction
        ).filter(
            Patient.status == 'oczekujący'
        ).order_by(
            TriagePrediction.kategoria_triazu.asc(),  # 1 (najwyższy priorytet) jako pierwszy
            Patient.data_przyjecia.asc()  # Starsi pacjenci pierwsi
        ).all()
        
        return [PatientWithPrediction.model_validate(p) for p in patients]
    
    @staticmethod
    def change_patient_status(
        db: Session,
        patient_id: int,
        new_status: str,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> Patient:
        """
        Zmienia status pacjenta
        
        Args:
            db: Sesja bazy danych
            patient_id: ID pacjenta
            new_status: Nowy status
            user_id: ID użytkownika
            ip_address: Adres IP
            
        Returns:
            Zaktualizowany pacjent
            
        Raises:
            HTTPException: Jeśli pacjent nie istnieje lub status jest nieprawidłowy
        """
        valid_statuses = ['oczekujący', 'w_leczeniu', 'wypisany', 'przekazany']
        
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        old_status = patient.status
        patient.status = new_status
        db.commit()
        db.refresh(patient)
        
        log_action(
            db=db,
            user_id=user_id,
            action="CHANGE_PATIENT_STATUS",
            table_name="patients",
            record_id=patient_id,
            old_values={"status": old_status},
            new_values={"status": new_status},
            ip_address=ip_address
        )
        
        return patient
    
    @staticmethod
    def search_patients(
        db: Session,
        query: str,
        limit: int = 20
    ) -> List[PatientListItem]:
        """
        Wyszukuje pacjentów
        
        Args:
            db: Sesja bazy danych
            query: Zapytanie wyszukiwania
            limit: Limit wyników
            
        Returns:
            Lista znalezionych pacjentów
        """
        patients = db.query(Patient).filter(
            (Patient.id.cast(str).like(f"%{query}%")) |
            (Patient.szablon_przypadku.like(f"%{query}%"))
        ).order_by(
            Patient.data_przyjecia.desc()
        ).limit(limit).all()
        
        return [PatientListItem.model_validate(p) for p in patients]
