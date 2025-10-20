import numpy as np
from app.ml.model_loader import model_loader
from app.ml.preprocessor import preprocessor

class TriagePredictor:
    """Klasa do wykonywania predykcji triaży"""
    
    def __init__(self):
        self.model = model_loader.load_latest_model()
    
    def predict(self, patient_data: dict) -> dict:
        """
        Wykonuje predykcję kategorii triaży
        
        Args:
            patient_data: Dane pacjenta (surowe)
        
        Returns:
            Dict z kategorią i prawdopodobieństwami
        """
        # 1. Preprocessing
        X = preprocessor.transform(patient_data)
        
        # 2. Predykcja
        category = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        return {
            "category": int(category),
            "probabilities": {
                "1": float(probabilities[0]),
                "2": float(probabilities[1]),
                "3": float(probabilities[2]),
                "4": float(probabilities[3]),
                "5": float(probabilities[4])
            },
            "confidence": float(max(probabilities))
        }

predictor = TriagePredictor()
