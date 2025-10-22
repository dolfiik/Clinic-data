from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from decimal import Decimal

from app.models import Patient, TriagePrediction, User
from app.schemas import (
    TriagePredictionCreate,
    TriagePredictionResponse,
    TriagePredictResponse,
    TriageStatsResponse,
    DailyTriageStats,
    CategoryDistribution,
    TriageAnalytics
)
from app.services.audit_service import log_action
from app.ml.predictor import predictor

CATEGORY_TO_DEPARTMENT = {
    1: "SOR",  # Natychmiastowy
    2: "SOR",  # Pilny
    3: "Interna",  # Stabilny
    4: "Interna",  # Niski priorytet
    5: "Interna"  # Bardzo niski
}

TEMPLATE_TO_DEPARTMENT = {
    "zawał_STEMI": "Kardiologia",
    "udar_ciężki": "Neurologia",
    "uraz_wielonarządowy": "Chirurgia",
    "zapalenie_płuc_ciężkie": "Interna",
    "zapalenie_wyrostka": "Chirurgia",
    "silne_krwawienie": "Chirurgia",
    "złamanie_proste": "Ortopedia",
    "infekcja_moczu": "Interna",
    "zaostrzenie_astmy": "Interna",
    "ból_brzucha_łagodny": "Interna",
    "skręcenie_lekkie": "Ortopedia",
    "migrena": "Neurologia",
    "przeziębienie": "Interna",
    "kontrola": "Interna",
    "receptura": "Interna"
}

class TriageService:
    """Service do zarządzania triażem i predykcjami ML"""
    
    @staticmethod
    def predict_triage(
        db: Session,
        patient_id: int,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> TriagePredictResponse:
        """
        Wykonuje predykcję triaży dla pacjenta
        
        Args:
            db: Sesja bazy danych
            patient_id: ID pacjenta
            user_id: ID użytkownika wykonującego predykcję
            ip_address: Adres IP
            
        Returns:
            Wynik predykcji
            
        Raises:
            HTTPException: Jeśli pacjent nie istnieje lub już ma predykcję
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        existing_prediction = db.query(TriagePrediction).filter(
            TriagePrediction.patient_id == patient_id
        ).first()
        
        if existing_prediction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient already has a triage prediction"
            )
        
        patient_data = {
            "wiek": patient.wiek,
            "plec": patient.plec,
            "tetno": float(patient.tetno) if patient.tetno else None,
            "cisnienie_skurczowe": float(patient.cisnienie_skurczowe) if patient.cisnienie_skurczowe else None,
            "cisnienie_rozkurczowe": float(patient.cisnienie_rozkurczowe) if patient.cisnienie_rozkurczowe else None,
            "temperatura": float(patient.temperatura) if patient.temperatura else None,
            "saturacja": float(patient.saturacja) if patient.saturacja else None,
            "gcs": patient.gcs,
            "bol": patient.bol,
            "czestotliwosc_oddechow": float(patient.czestotliwosc_oddechow) if patient.czestotliwosc_oddechow else None,
            "czas_od_objawow_h": float(patient.czas_od_objawow_h) if patient.czas_od_objawow_h else None,
            "szablon_przypadku": patient.szablon_przypadku
        }
        
        try:
            prediction_result = predictor.predict(patient_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model prediction failed: {str(e)}"
            )
        
        category = prediction_result["category"]
        probabilities = prediction_result["probabilities"]
        confidence = prediction_result["confidence"]
        
        if patient.szablon_przypadku and patient.szablon_przypadku in TEMPLATE_TO_DEPARTMENT:
            assigned_department = TEMPLATE_TO_DEPARTMENT[patient.szablon_przypadku]
        else:
            assigned_department = CATEGORY_TO_DEPARTMENT.get(category, "SOR")
        
        prediction = TriagePrediction(
            patient_id=patient_id,
            kategoria_triazu=category,
            prob_kat_1=Decimal(str(probabilities["1"])),
            prob_kat_2=Decimal(str(probabilities["2"])),
            prob_kat_3=Decimal(str(probabilities["3"])),
            prob_kat_4=Decimal(str(probabilities["4"])),
            prob_kat_5=Decimal(str(probabilities["5"])),
            przypisany_oddzial=assigned_department,
            oddzial_docelowy=assigned_department,
            model_version=prediction_result.get("model_version", "unknown"),
            confidence_score=Decimal(str(confidence))
        )
        
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        log_action(
            db=db,
            user_id=user_id,
            action="PREDICT_TRIAGE",
            table_name="triage_predictions",
            record_id=prediction.id,
            new_values={
                "patient_id": patient_id,
                "kategoria_triazu": category,
                "confidence": float(confidence),
                "przypisany_oddzial": assigned_department
            },
            ip_address=ip_address
        )
        
        return TriagePredictResponse(
            patient_id=patient_id,
            kategoria_triazu=category,
            probabilities=probabilities,
            przypisany_oddzial=assigned_department,
            confidence_score=confidence,
            model_version=prediction_result.get("model_version", "unknown")
        )
    
    @staticmethod
    def get_prediction(db: Session, patient_id: int) -> Optional[TriagePredictionResponse]:
        """
        Pobiera predykcję dla pacjenta
        
        Args:
            db: Sesja bazy danych
            patient_id: ID pacjenta
            
        Returns:
            Predykcja lub None
        """
        prediction = db.query(TriagePrediction).filter(
            TriagePrediction.patient_id == patient_id
        ).first()
        
        if not prediction:
            return None
        
        return TriagePredictionResponse.model_validate(prediction)
    
    @staticmethod
    def get_stats(db: Session) -> TriageStatsResponse:
        """
        Pobiera statystyki triaży
        
        Args:
            db: Sesja bazy danych
            
        Returns:
            Statystyki triaży
        """
        from sqlalchemy import func
        
        total_patients = db.query(Patient).count()
        
        by_category = db.query(
            TriagePrediction.kategoria_triazu,
            func.count(TriagePrediction.id)
        ).group_by(TriagePrediction.kategoria_triazu).all()
        
        category_dict = {str(cat): count for cat, count in by_category}
        
        by_department = db.query(
            TriagePrediction.przypisany_oddzial,
            func.count(TriagePrediction.id)
        ).group_by(TriagePrediction.przypisany_oddzial).all()
        
        department_dict = {dept: count for dept, count in by_department}
        
        avg_confidence = db.query(
            func.avg(TriagePrediction.confidence_score)
        ).scalar()
        
        return TriageStatsResponse(
            total_patients=total_patients,
            by_category=category_dict,
            by_department=department_dict,
            average_confidence=float(avg_confidence or 0),
            last_updated=datetime.now()
        )
    
    @staticmethod
    def get_daily_stats(db: Session, days: int = 7) -> List[DailyTriageStats]:
        """
        Pobiera dzienne statystyki triaży
        
        Args:
            db: Sesja bazy danych
            days: Liczba dni wstecz
            
        Returns:
            Lista dziennych statystyk
        """
        from sqlalchemy import func, extract, case
        
        date_from = datetime.now() - timedelta(days=days)
        
        stats = db.query(
            func.date(Patient.data_przyjecia).label('data'),
            func.count(Patient.id).label('liczba_pacjentow'),
            func.sum(case((TriagePrediction.kategoria_triazu == 1, 1), else_=0)).label('kat_1'),
            func.sum(case((TriagePrediction.kategoria_triazu == 2, 1), else_=0)).label('kat_2'),
            func.sum(case((TriagePrediction.kategoria_triazu == 3, 1), else_=0)).label('kat_3'),
            func.sum(case((TriagePrediction.kategoria_triazu == 4, 1), else_=0)).label('kat_4'),
            func.sum(case((TriagePrediction.kategoria_triazu == 5, 1), else_=0)).label('kat_5'),
            func.avg(
                extract('epoch', TriagePrediction.predicted_at - Patient.data_przyjecia) / 60
            ).label('avg_czas_min'),
            func.avg(TriagePrediction.confidence_score).label('avg_confidence')
        ).join(
            TriagePrediction, Patient.id == TriagePrediction.patient_id, isouter=True
        ).filter(
            Patient.data_przyjecia >= date_from
        ).group_by(
            func.date(Patient.data_przyjecia)
        ).order_by(
            func.date(Patient.data_przyjecia).desc()
        ).all()
        
        result = []
        for stat in stats:
            result.append(DailyTriageStats(
                data=stat.data,
                liczba_pacjentow=stat.liczba_pacjentow,
                kat_1_natychmiastowy=stat.kat_1 or 0,
                kat_2_pilny=stat.kat_2 or 0,
                kat_3_stabilny=stat.kat_3 or 0,
                kat_4_niski=stat.kat_4 or 0,
                kat_5_bardzo_niski=stat.kat_5 or 0,
                avg_czas_do_triazu_min=float(stat.avg_czas_min) if stat.avg_czas_min else None,
                avg_confidence=float(stat.avg_confidence) if stat.avg_confidence else None
            ))
        
        return result
    
    @staticmethod
    def get_analytics(
        db: Session,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> TriageAnalytics:
        """
        Pobiera zaawansowaną analitykę
        
        Args:
            db: Sesja bazy danych
            date_from: Data od
            date_to: Data do
            
        Returns:
            Analityka triaży
        """
        from sqlalchemy import func
        
        query = db.query(TriagePrediction)
        
        if date_from:
            query = query.filter(TriagePrediction.predicted_at >= date_from)
        else:
            date_from = datetime.now() - timedelta(days=30)
        
        if date_to:
            query = query.filter(TriagePrediction.predicted_at <= date_to)
        else:
            date_to = datetime.now()
        
        total = query.count()
        
        category_counts = db.query(
            TriagePrediction.kategoria_triazu,
            func.count(TriagePrediction.id)
        ).filter(
            TriagePrediction.predicted_at >= date_from,
            TriagePrediction.predicted_at <= date_to
        ).group_by(TriagePrediction.kategoria_triazu).all()
        
        category_labels = {
            1: "Natychmiastowy",
            2: "Pilny",
            3: "Stabilny",
            4: "Niski priorytet",
            5: "Bardzo niski"
        }
        
        distributions = []
        for cat, count in category_counts:
            percentage = (count / total * 100) if total > 0 else 0
            distributions.append(CategoryDistribution(
                category=cat,
                count=count,
                percentage=round(percentage, 2),
                label=category_labels[cat]
            ))
        
        distributions.sort(key=lambda x: x.category)
        
        avg_confidence = db.query(
            func.avg(TriagePrediction.confidence_score)
        ).filter(
            TriagePrediction.predicted_at >= date_from,
            TriagePrediction.predicted_at <= date_to
        ).scalar()
        
        model_version = db.query(
            TriagePrediction.model_version
        ).filter(
            TriagePrediction.predicted_at >= date_from,
            TriagePrediction.predicted_at <= date_to
        ).group_by(
            TriagePrediction.model_version
        ).order_by(
            func.count(TriagePrediction.id).desc()
        ).first()
        
        return TriageAnalytics(
            total_predictions=total,
            category_distribution=distributions,
            average_confidence=float(avg_confidence or 0),
            model_version=model_version[0] if model_version else "unknown",
            period_start=date_from,
            period_end=date_to
        )
