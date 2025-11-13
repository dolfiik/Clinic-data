from sqlalchemy.orm import Session
from typing import Dict, Optional
from fastapi import HTTPException, status

from app.ml.predictor import predictor as triage_predictor
from app.services.occupancy_service import OccupancyService, occupancy_predictor
from app.services.allocation_service import AllocationService, allocation_predictor
from app.services.department_service import DepartmentService
from app.schemas import TriagePreviewRequest, TriagePreviewResponse


class TriageOrchestrator:
    """
    Orchestrator łączący 3 modele:
    1. Model Triaż → kategoria (1-5)
    2. Model Occupancy → prognozy obłożenia
    3. Model Allocation → optymalny oddział
    """
    
    @staticmethod
    def predict_full(
        db: Session,
        preview_request: TriagePreviewRequest
    ) -> TriagePreviewResponse:
        """
        Wykonuje pełny pipeline 3 modeli
        
        Pipeline:
        1. Model 1 (Triaż): kategoria + confidence
        2. Model 2 (LSTM): prognozy obłożenia za 1h, 3h
        3. Model 3 (Allocation): optymalny oddział
        
        Args:
            db: Sesja bazy danych
            preview_request: Dane pacjenta
            
        Returns:
            Kompletna predykcja z rekomendacjami
        """
        
        patient_data = {
            "wiek": preview_request.wiek,
            "plec": preview_request.plec,
            "tetno": float(preview_request.tetno),
            "cisnienie_skurczowe": float(preview_request.cisnienie_skurczowe),
            "cisnienie_rozkurczowe": float(preview_request.cisnienie_rozkurczowe),
            "temperatura": float(preview_request.temperatura),
            "saturacja": float(preview_request.saturacja),
            "gcs": preview_request.gcs,
            "bol": preview_request.bol,
            "czestotliwosc_oddechow": float(preview_request.czestotliwosc_oddechow),
            "czas_od_objawow_h": float(preview_request.czas_od_objawow_h),
            "szablon_przypadku": preview_request.szablon_przypadku
        }
        
        try:
            triage_result = triage_predictor.predict(patient_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model 1 (Triaż) failed: {str(e)}"
            )
        
        category = triage_result["category"]
        triage_probabilities = triage_result["probabilities"]
        triage_confidence = triage_result["confidence"]
        
        try:
            occupancy_data = OccupancyService.get_forecast(db, hours_ahead=3)
            current_occupancy = occupancy_data["current"]
            future_occupancy = occupancy_data.get("forecast", {})
        except Exception as e:
            print(f" Warning: Model 2 (Occupancy) failed: {e}")
            current_occupancy = DepartmentService.get_current_occupancy(db)
            future_occupancy = {}
        
        try:
            allocation_result = AllocationService.recommend_department(
                patient_data=patient_data,
                triage_category=category,
                current_occupancy=current_occupancy,
                future_occupancy=future_occupancy
            )
            
            assigned_department = allocation_result["department"]
            allocation_confidence = allocation_result["confidence"]
            alternatives = allocation_result["alternatives"]
            
        except Exception as e:
            print(f" Warning: Model 3 (Allocation) failed: {e}")
            assigned_department = TriageOrchestrator._fallback_department_assignment(
                category, 
                preview_request.szablon_przypadku
            )
            allocation_confidence = 0.5
            alternatives = []
        
        
        category_descriptions = {
            1: "NATYCHMIASTOWY - Resuscytacja, zagrożenie życia",
            2: "PILNY - Bardzo pilny, ciężki stan",
            3: "STABILNY - Pilny, stabilny pacjent",
            4: "NISKI PRIORYTET - Mniej pilny",
            5: "BARDZO NISKI - Nieistotny"
        }
        
        priority_labels = {
            1: "RESUSCYTACJA",
            2: "CIĘŻKI STAN",
            3: "STABILNY",
            4: "NISKI",
            5: "BARDZO NISKI"
        }
        
        available_departments = list(current_occupancy.keys())
        
        response = TriagePreviewResponse(
            kategoria_triazu=category,
            probabilities=triage_probabilities,
            przypisany_oddzial=assigned_department,
            confidence_score=allocation_confidence,
            model_version=f"v1:{triage_result.get('model_version', 'unknown')}",
            priorytet=priority_labels[category],
            opis_kategorii=category_descriptions[category],
            dostepne_oddzialy=available_departments
        )
        
        response.triage_confidence = triage_confidence
        response.allocation_confidence = allocation_confidence
        response.alternatives = alternatives
        response.current_occupancy = current_occupancy
        response.occupancy_forecast = future_occupancy
        
        return response
    
    @staticmethod
    def _fallback_department_assignment(
        category: int, 
        szablon: Optional[str]
    ) -> str:
        """
        Fallback logika przypisywania oddziału (gdy Model 3 nie działa)
        
        Args:
            category: Kategoria triażu
            szablon: Szablon przypadku
            
        Returns:
            Nazwa oddziału
        """
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
        
        CATEGORY_TO_DEPARTMENT = {
            1: "SOR",
            2: "SOR",
            3: "Interna",
            4: "Interna",
            5: "Interna"
        }
        
        if szablon and szablon in TEMPLATE_TO_DEPARTMENT:
            return TEMPLATE_TO_DEPARTMENT[szablon]
        
        return CATEGORY_TO_DEPARTMENT.get(category, "SOR")
    
    @staticmethod
    def get_models_info() -> Dict:
        """
        Zwraca informacje o wszystkich 3 modelach
        
        Returns:
            {
                "model_1_triage": {...},
                "model_2_occupancy": {...},
                "model_3_allocation": {...}
            }
        """
        return {
            "model_1_triage": triage_predictor.get_model_info(),
            "model_2_occupancy": occupancy_predictor.get_model_info(),
            "model_3_allocation": allocation_predictor.get_model_info()
        }
