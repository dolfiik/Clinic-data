from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import numpy as np
import tensorflow as tf
from tensorflow import keras

from app.models import DepartmentOccupancy
from app.core.config import settings

DEPARTMENTS = ["SOR", "Interna", "Kardiologia", "Chirurgia", 
               "Ortopedia", "Neurologia", "Pediatria", "Ginekologia"]

SEQUENCE_LENGTH = 24  # 24 godziny historii
N_DEPARTMENTS = len(DEPARTMENTS)

class OccupancyPredictor:
    """Klasa do prognozowania obłożenia oddziałów używając LSTM"""
    
    def __init__(self):
        self.model = None
        self.seq_scaler = None
        self.static_scaler = None
        self.target_scaler = None
        self.model_version = None
        self.model_path = Path(settings.MODEL_PATH)
        
    def load_model(self):
        """Wczytuje najnowszy model LSTM z dysku"""
        print(" Wczytywanie LSTM Model 2 (Occupancy Forecasting)...")
        
        latest_info_path = self.model_path / 'latest_model.json'
        
        if not latest_info_path.exists():
            raise FileNotFoundError(
                "Nie znaleziono latest_model.json dla Model 2 "
            )
        
        import json
        with open(latest_info_path, 'r') as f:
            latest_info = json.load(f)
        
        model_filename = (
            latest_info.get('model_file') or 
            latest_info.get('model_filename') or
            latest_info.get('model_path')  
        )
        
        scalers_filename = (
            latest_info.get('scalers_file') or 
            latest_info.get('scalers_filename') or
            latest_info.get('scalers_path')  
        )
        
        self.model_version = latest_info.get('version', '2.0.0')
        
        if not model_filename:
            raise FileNotFoundError(
                f"latest_model.json nie zawiera ścieżki do modelu. "
                f"Znalezione klucze: {list(latest_info.keys())}"
            )
        
        if not scalers_filename:
            raise FileNotFoundError(
                f"latest_model.json nie zawiera ścieżki do scalers. "
                f"Znalezione klucze: {list(latest_info.keys())}"
            )
        
        from pathlib import Path
        
        if isinstance(model_filename, str) and model_filename.startswith('models/'):
            model_filename = model_filename.replace('models/', '')
        if isinstance(scalers_filename, str) and scalers_filename.startswith('models/'):
            scalers_filename = scalers_filename.replace('models/', '')
        
        model_file = self.model_path / model_filename
        if not model_file.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_file}\n"
                f"Sprawdź czy plik istnieje: ls -la {self.model_path}"
            )
        
        self.model = keras.models.load_model(str(model_file))
        print(f" Model wczytany: {model_filename}")
        
        scalers_file = self.model_path / scalers_filename
        if not scalers_file.exists():
            raise FileNotFoundError(
                f"Scalers file not found: {scalers_file}\n"
                f"Sprawdź czy plik istnieje: ls -la {self.model_path}"
            )
        
        with open(scalers_file, 'rb') as f:
            scalers = pickle.load(f)
        
        self.seq_scaler = scalers['seq_scaler']
        self.static_scaler = scalers['static_scaler']
        self.target_scaler = scalers['target_scaler']
        
        print(f" Scalers wczytane: {scalers_filename}")
        print(f" Model v{self.model_version} gotowy do użycia")
        print(f" MAE: {latest_info.get('mae', 'N/A')}")
    
    def prepare_sequences(
        self, 
        occupancy_history: List[DepartmentOccupancy]
    ) -> tuple:
        """
        Przygotowuje sekwencje dla LSTM
        
        Args:
            occupancy_history: Historia obłożenia (24h)
            
        Returns:
            (X_seq, X_static) gotowe do predykcji
        """
        if len(occupancy_history) < SEQUENCE_LENGTH:
            raise ValueError(
                f"Potrzeba {SEQUENCE_LENGTH}h historii, mamy tylko {len(occupancy_history)}"
            )
        
        recent_history = occupancy_history[-SEQUENCE_LENGTH:]
        
        sequence = []
        for record in recent_history:
            values = [
                record.sor,
                record.interna,
                record.kardiologia,
                record.chirurgia,
                record.ortopedia,
                record.neurologia,
                record.pediatria,
                record.ginekologia
            ]
            sequence.append(values)
        
        X_seq = np.array([sequence], dtype=np.float32)  # (1, 24, 8)
        
        last_timestamp = recent_history[-1].timestamp
        hour = last_timestamp.hour
        day_of_week = last_timestamp.weekday()
        month = last_timestamp.month
        is_weekend = 1 if day_of_week >= 5 else 0
        
        X_static = np.array([[hour, day_of_week, month, is_weekend]], dtype=np.float32)
        
        X_seq_scaled = self.seq_scaler.transform(
            X_seq.reshape(-1, N_DEPARTMENTS)
        ).reshape(X_seq.shape)
        
        X_static_scaled = self.static_scaler.transform(X_static)
        
        return X_seq_scaled, X_static_scaled
    
    def predict_future_occupancy(
        self, 
        occupancy_history: List[DepartmentOccupancy],
        hours_ahead: int = 3
    ) -> Dict[str, Dict[str, int]]:
        """
        Prognozuje obłożenie na kolejne godziny
        
        Args:
            occupancy_history: Historia obłożenia (minimum 24h)
            hours_ahead: Ile godzin w przód (domyślnie 3)
            
        Returns:
            Słownik: {
                "hour_1": {"SOR": 18, "Interna": 42, ...},
                "hour_2": {...},
                "hour_3": {...}
            }
        """
        if self.model is None:
            raise RuntimeError("Model nie został wczytany! Wywołaj load_model() najpierw.")
        
        X_seq, X_static = self.prepare_sequences(occupancy_history)
        
        predictions = []
        current_seq = X_seq.copy()
        
        for _ in range(hours_ahead):
            y_pred_scaled = self.model.predict(
                [current_seq, X_static], 
                verbose=0
            )
            
            y_pred = self.target_scaler.inverse_transform(y_pred_scaled)[0]
            
            y_pred_int = np.round(y_pred).astype(int)
            
            y_pred_int = np.maximum(y_pred_int, 0)
            
            predictions.append(y_pred_int)
            
            new_seq = np.concatenate([current_seq[0, 1:, :], y_pred_scaled], axis=0)
            current_seq = new_seq.reshape(1, SEQUENCE_LENGTH, N_DEPARTMENTS)
        
        result = {}
        for i, pred in enumerate(predictions):
            hour_key = f"hour_{i+1}"
            result[hour_key] = {
                dept: int(pred[j]) for j, dept in enumerate(DEPARTMENTS)
            }
        
        return result
    
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
            "type": "LSTM",
            "departments": DEPARTMENTS,
            "sequence_length": SEQUENCE_LENGTH,
            "prediction_horizon": "1-6 hours"
        }


occupancy_predictor = OccupancyPredictor()


class OccupancyService:
    """Service do zarządzania prognozami obłożenia"""
    
    @staticmethod
    def get_forecast(
        db: Session,
        hours_ahead: int = 3
    ) -> Dict:
        """
        Pobiera prognozy obłożenia dla wszystkich oddziałów
        
        Args:
            db: Sesja bazy danych
            hours_ahead: Ile godzin w przód (1-6)
            
        Returns:
            {
                "current": {"SOR": 18, ...},
                "forecast": {
                    "SOR": {"hour_1": 19, "hour_2": 20, "hour_3": 21},
                    ...
                },
                "timestamp": "2025-11-03T17:00:00Z",
                "model_version": "2.0.0"
            }
        """
        latest = db.query(DepartmentOccupancy)\
            .order_by(DepartmentOccupancy.timestamp.desc())\
            .first()
        
        if not latest:
            raise ValueError("Brak danych o obłożeniu w bazie")
        
        current_occupancy = {
            "SOR": latest.sor,
            "Interna": latest.interna,
            "Kardiologia": latest.kardiologia,
            "Chirurgia": latest.chirurgia,
            "Ortopedia": latest.ortopedia,
            "Neurologia": latest.neurologia,
            "Pediatria": latest.pediatria,
            "Ginekologia": latest.ginekologia
        }
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        history = db.query(DepartmentOccupancy)\
            .filter(DepartmentOccupancy.timestamp >= cutoff_time)\
            .order_by(DepartmentOccupancy.timestamp.asc())\
            .all()
        
        if len(history) < SEQUENCE_LENGTH:
            return {
                "current": current_occupancy,
                "forecast": {},
                "timestamp": latest.timestamp.isoformat(),
                "model_version": "N/A",
                "warning": f"Insufficient history data (need {SEQUENCE_LENGTH}h, have {len(history)}h)"
            }
        
        try:
            forecast_raw = occupancy_predictor.predict_future_occupancy(
                history, 
                hours_ahead=hours_ahead
            )
            
            forecast_by_dept = {}
            for dept in DEPARTMENTS:
                forecast_by_dept[dept] = {
                    hour_key: forecast_raw[hour_key][dept]
                    for hour_key in forecast_raw.keys()
                }
            
            return {
                "current": current_occupancy,
                "forecast": forecast_by_dept,
                "timestamp": datetime.now().isoformat(),
                "model_version": occupancy_predictor.model_version
            }
            
        except Exception as e:
            print(f" Błąd predykcji obłożenia: {e}")
            return {
                "current": current_occupancy,
                "forecast": {},
                "timestamp": latest.timestamp.isoformat(),
                "model_version": "N/A",
                "error": str(e)
            }
