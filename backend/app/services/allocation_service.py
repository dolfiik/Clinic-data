from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from datetime import datetime

from app.core.config import settings

DEPARTMENTS = ["SOR", "Interna", "Kardiologia", "Chirurgia", "Ortopedia", "Neurologia"]

DEPARTMENT_CAPACITY = {
    "SOR": 25,
    "Interna": 50,
    "Kardiologia": 30,
    "Chirurgia": 35,
    "Ortopedia": 25,
    "Neurologia": 20
}

class AllocationPredictor:
    """Klasa do przewidywania optymalnego oddziału dla pacjenta"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = None
        self.model_version = None
        self.model_path = Path(settings.MODEL_PATH)
    
    def load_model(self):
        """Wczytuje najnowszy model alokacji z dysku"""
        print(" Wczytywanie Model 3 (Department Allocation)")
        
        model_files = list(self.model_path.glob('allocation_*_v3.*.pkl'))
        
        if not model_files:
            raise FileNotFoundError(
                "Nie znaleziono modelu alokacji (allocation_*.pkl). Wytrenuj Model 3!"
            )
        
        model_file = sorted(model_files)[-1]
        
        with open(model_file, 'rb') as f:
            self.model = pickle.load(f)
        
        print(f"✓ Model załadowany: {model_file.name}")
        
        artifact_pattern = model_file.name.replace('allocation_', 'allocation_artifacts_')
        artifact_pattern = artifact_pattern.replace(model_file.stem.split('_v3')[0], '*')
        
        artifact_files = list(self.model_path.glob('allocation_artifacts_v3*.pkl'))
        
        if not artifact_files:
            raise FileNotFoundError(
                "Nie znaleziono artifacts dla modelu alokacji"
            )
        
        artifact_file = sorted(artifact_files)[-1]
        
        with open(artifact_file, 'rb') as f:
            artifacts = pickle.load(f)
        
        self.scaler = artifacts['scaler']
        self.label_encoder = artifacts['label_encoder']
        self.feature_columns = artifacts['feature_columns']
        self.model_version = artifacts.get('model_version', '3.0.0')
        
        print(f" Model v{self.model_version} gotowy do użycia")
        print(f" Liczba cech: {len(self.feature_columns)}")
    
    def prepare_features(
        self,
        patient_data: Dict,
        triage_category: int,
        current_occupancy: Dict[str, int],
        future_occupancy: Dict[str, Dict[str, int]]
    ) -> pd.DataFrame:
        """
        Przygotowuje cechy dla modelu alokacji
        
        Args:
            patient_data: Dane pacjenta (wiek, płeć, parametry vitalne, etc.)
            triage_category: Kategoria triażu z Model 1 (1-5)
            current_occupancy: Obecne obłożenie oddziałów
            future_occupancy: Prognozy obłożenia z Model 2
            
        Returns:
            DataFrame z cechami gotowymi do predykcji
        """
        features = {}
        
        features['wiek'] = patient_data['wiek']
        features['płeć_encoded'] = 1 if patient_data['plec'] == 'M' else 0
        features['kategoria_triażu'] = triage_category
        features['tętno'] = patient_data['tetno']
        features['ciśnienie_skurczowe'] = patient_data['cisnienie_skurczowe']
        features['ciśnienie_rozkurczowe'] = patient_data['cisnienie_rozkurczowe']
        features['temperatura'] = patient_data['temperatura']
        features['saturacja'] = patient_data['saturacja']
        features['GCS'] = patient_data.get('gcs', 15)
        features['ból'] = patient_data.get('bol', 0)
        features['częstotliwość_oddechów'] = patient_data.get('czestotliwosc_oddechow', 18)
        features['czas_od_objawów_h'] = patient_data.get('czas_od_objawow_h', 0)
        
        now = datetime.now()
        features['godzina'] = now.hour
        features['dzien_tygodnia'] = now.weekday()
        features['miesiac'] = now.month
        features['czy_weekend'] = 1 if now.weekday() >= 5 else 0
        
        for dept in DEPARTMENTS:
            occ = current_occupancy.get(dept, 0)
            capacity = DEPARTMENT_CAPACITY[dept]
            
            features[f'occ_{dept}'] = occ
            features[f'occ_pct_{dept}'] = (occ / capacity) * 100
            features[f'overcrowded_{dept}'] = 1 if (occ / capacity) > 0.8 else 0
        
        for dept in DEPARTMENTS:
            dept_forecast = future_occupancy.get(dept, {})
            capacity = DEPARTMENT_CAPACITY[dept]
            
            # Za 1h
            future_1h = dept_forecast.get('hour_1', current_occupancy.get(dept, 0))
            features[f'future_occ_1h_{dept}'] = future_1h
            features[f'future_pct_1h_{dept}'] = (future_1h / capacity) * 100
            
            # Za 3h
            future_3h = dept_forecast.get('hour_3', current_occupancy.get(dept, 0))
            features[f'future_occ_3h_{dept}'] = future_3h
            features[f'future_pct_3h_{dept}'] = (future_3h / capacity) * 100
            
            # Delta (zmiana obłożenia)
            features[f'delta_occ_{dept}'] = future_3h - current_occupancy.get(dept, 0)
        
        for dept in DEPARTMENTS:
            features[f'oddział_{dept}'] = 0  # Wypełnimy later w pętli predykcji
        
        szablon = patient_data.get('szablon_przypadku')
        
        all_templates = [
            'ból_brzucha_łagodny', 'infekcja_moczu', 'kontrola', 'migrena',
            'przeziębienie', 'receptura', 'silne_krwawienie', 'skręcenie_lekkie',
            'udar_ciężki', 'uraz_wielonarządowy', 'zaostrzenie_astmy',
            'zapalenie_płuc_ciężkie', 'zapalenie_wyrostka', 'zawał_STEMI',
            'złamanie_proste'
        ]
        
        for template in all_templates:
            features[f'szablon_{template}'] = 1 if szablon == template else 0
        
        df = pd.DataFrame([features])
        
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        df = df[self.feature_columns]
        
        return df
    
    def predict_department(
        self,
        patient_data: Dict,
        triage_category: int,
        current_occupancy: Dict[str, int],
        future_occupancy: Dict[str, Dict[str, int]]
    ) -> Dict:
        """
        Przewiduje optymalny oddział dla pacjenta
        
        Args:
            patient_data: Dane pacjenta
            triage_category: Kategoria triażu (1-5)
            current_occupancy: Obecne obłożenie
            future_occupancy: Prognozy obłożenia
            
        Returns:
            {
                "department": "Kardiologia",
                "confidence": 0.92,
                "probabilities": {"Kardiologia": 0.92, "Interna": 0.05, ...},
                "alternatives": [
                    {"name": "Interna", "confidence": 0.78},
                    ...
                ]
            }
        """
        if self.model is None:
            raise RuntimeError("Model nie został wczytany! Wywołaj load_model() najpierw.")
        
        X = self.prepare_features(
            patient_data,
            triage_category,
            current_occupancy,
            future_occupancy
        )
        
        X_scaled = self.scaler.transform(X)
        
        y_pred = self.model.predict(X_scaled)[0]
        y_proba = self.model.predict_proba(X_scaled)[0]
        
        department = self.label_encoder.inverse_transform([y_pred])[0]
        confidence = float(y_proba.max())
        
        probabilities = {
            self.label_encoder.inverse_transform([i])[0]: float(prob)
            for i, prob in enumerate(y_proba)
        }
        
        alternatives = []
        sorted_indices = np.argsort(y_proba)[::-1][1:4]  
        
        for idx in sorted_indices:
            alt_dept = self.label_encoder.inverse_transform([idx])[0]
            alt_conf = float(y_proba[idx])
            
            alternatives.append({
                "name": alt_dept,
                "confidence": alt_conf,
                "current_occupancy": current_occupancy.get(alt_dept, 0),
                "capacity": DEPARTMENT_CAPACITY.get(alt_dept, 30),
                "percentage": round((current_occupancy.get(alt_dept, 0) / DEPARTMENT_CAPACITY.get(alt_dept, 30)) * 100)
            })
        
        return {
            "department": department,
            "confidence": confidence,
            "probabilities": probabilities,
            "alternatives": alternatives,
            "model_version": self.model_version
        }
    
    def get_model_info(self) -> dict:
        """Zwraca informacje o modelu"""
        if self.model is None:
            return {
                "loaded": False,
                "error": "Model not loaded"
            }
        
        return {
            "loaded": True,
            "version": self.model_version,
            "type": type(self.model).__name__,
            "departments": DEPARTMENTS,
            "n_features": len(self.feature_columns)
        }


allocation_predictor = AllocationPredictor()


class AllocationService:
    """Service do zarządzania alokacją pacjentów"""
    
    @staticmethod
    def recommend_department(
        patient_data: Dict,
        triage_category: int,
        current_occupancy: Dict[str, int],
        future_occupancy: Dict[str, Dict[str, int]]
    ) -> Dict:
        """
        Rekomenduje optymalny oddział dla pacjenta
        
        Args:
            patient_data: Dane pacjenta
            triage_category: Kategoria triażu
            current_occupancy: Obecne obłożenie
            future_occupancy: Prognozy obłożenia
            
        Returns:
            Rekomendacja z confidence i alternatywami
        """
        return allocation_predictor.predict_department(
            patient_data,
            triage_category,
            current_occupancy,
            future_occupancy
        )
