import numpy as np
from typing import Dict, Any
from fastapi import HTTPException, status

from app.ml.model_loader import model_loader
from app.ml.preprocessor import preprocessor

class TriagePredictor:
    """Klasa do wykonywania predykcji triaży"""
    
    def __init__(self):
        """Inicjalizacja predictora - ładuje model"""
        self.model = None
        self.model_version = "unknown"
        self._load_model()
    
    def _load_model(self):
        """Ładuje model ML"""
        try:
            self.model = model_loader.load_latest_model()
            model_info = model_loader.get_model_info()
            self.model_version = model_info.get('version', 'unknown')
            print(f"Predictor zainicjalizowany z modelem: {self.model_version}")
        except Exception as e:
            print(f"Błąd ładowania modelu: {e}")
            print("  Predictor będzie działał bez modelu (tylko dla testów)")
            self.model = None
    
    def predict(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wykonuje predykcję kategorii triaży
        
        Args:
            patient_data: Dane pacjenta (surowe)
            
        Returns:
            Dict z kategorią i prawdopodobieństwami:
            {
                "category": int,
                "probabilities": {"1": float, "2": float, ...},
                "confidence": float,
                "model_version": str
            }
            
        Raises:
            HTTPException: Jeśli model nie jest załadowany lub dane są nieprawidłowe
        """
        if self.model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML model not loaded. Check server logs for details."
            )
        
        is_valid, error_message = preprocessor.validate_input(patient_data)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid patient data: {error_message}"
            )
        
        try:
            X = preprocessor.transform(patient_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Preprocessing failed: {str(e)}"
            )
        
        try:
            category = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            confidence = float(max(probabilities))
            
            result = {
                "category": int(category),
                "probabilities": {
                    "1": float(probabilities[0]),
                    "2": float(probabilities[1]),
                    "3": float(probabilities[2]),
                    "4": float(probabilities[3]),
                    "5": float(probabilities[4])
                },
                "confidence": confidence,
                "model_version": self.model_version
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model prediction failed: {str(e)}"
            )
    
    def predict_batch(self, patients_data: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Wykonuje predykcję dla wielu pacjentów
        
        Args:
            patients_data: Lista danych pacjentów
            
        Returns:
            Lista wyników predykcji
        """
        results = []
        
        for patient_data in patients_data:
            try:
                result = self.predict(patient_data)
                results.append(result)
            except HTTPException as e:
                results.append({
                    "error": e.detail,
                    "status_code": e.status_code
                })
        
        return results
    
    def get_feature_importance(self, top_n: int = 20) -> Dict[str, float]:
        """
        Zwraca ważność cech (dla Random Forest)
        
        Args:
            top_n: Liczba najważniejszych cech do zwrócenia
            
        Returns:
            Słownik {feature_name: importance}
        """
        if self.model is None:
            return {}
        
        if not hasattr(self.model, 'feature_importances_'):
            return {}
        
        feature_names = preprocessor.get_feature_names()
        
        importances = self.model.feature_importances_
        feature_importance = dict(zip(feature_names, importances))
        
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return dict(sorted_features[:top_n])
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Zwraca informacje o modelu
        
        Returns:
            Słownik z informacjami
        """
        if self.model is None:
            return {
                "loaded": False,
                "error": "Model not loaded"
            }
        
        info = model_loader.get_model_info()
        info['model_version'] = self.model_version
        
        info['preprocessor'] = {
            "scaler_loaded": preprocessor.scaler is not None,
            "num_features": len(preprocessor.get_feature_names()),
            "templates": len(preprocessor.templates),
            "departments": len(preprocessor.departments)
        }
        
        return info
    
    def reload_model(self):
        """Przeładowuje model (np. po aktualizacji)"""
        print("Przeładowywanie modelu...")
        self._load_model()

predictor = TriagePredictor()
