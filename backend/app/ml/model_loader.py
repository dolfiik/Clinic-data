import pickle
from pathlib import Path
from typing import Optional
from app.core.config import settings

class ModelLoader:
    """Klasa do ładowania modeli ML"""
    
    def __init__(self):
        self.model = None
        self.model_path = None
        self.model_version = None
    
    def load_latest_model(self) -> any:
        """
        Ładuje najnowszy model z folderu models/
        
        Returns:
            Załadowany model
            
        Raises:
            FileNotFoundError: Jeśli nie znaleziono żadnych modeli
        """
        model_dir = Path(settings.MODEL_PATH)
        
        if not model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {model_dir}")
        
        # Znajdź najnowszy model Random Forest
        rf_models = list(model_dir.glob("random_forest*.pkl"))
        
        if not rf_models:
            raise FileNotFoundError(f"No Random Forest models found in {model_dir}")
        
        latest_model = max(rf_models, key=lambda p: p.stat().st_mtime)
        
        print(f"📦 Ładowanie modelu: {latest_model.name}")
        
        with open(latest_model, 'rb') as f:
            self.model = pickle.load(f)
        
        self.model_path = latest_model
        
        filename = latest_model.stem
        parts = filename.split('_')
        
        if len(parts) >= 3:
            date_part = parts[-2]
            time_part = parts[-1]
            self.model_version = f"rf_{date_part}_{time_part}"
        else:
            self.model_version = filename
        
        print(f"Model załadowany: {self.model_version}")
        print(f"Typ: {type(self.model).__name__}")
        
        if hasattr(self.model, 'n_estimators'):
            print(f"  Liczba drzew: {self.model.n_estimators}")
        
        return self.model
    
    def load_specific_model(self, model_path: str) -> any:
        """
        Ładuje konkretny model
        
        Args:
            model_path: Ścieżka do modelu
            
        Returns:
            Załadowany model
            
        Raises:
            FileNotFoundError: Jeśli model nie istnieje
        """
        model_file = Path(model_path)
        
        if not model_file.exists():
            raise FileNotFoundError(f"Model not found: {model_file}")
        
        print(f"Ładowanie modelu: {model_file.name}")
        
        with open(model_file, 'rb') as f:
            self.model = pickle.load(f)
        
        self.model_path = model_file
        self.model_version = model_file.stem
        
        print(f"Model załadowany: {self.model_version}")
        
        return self.model
    
    def get_model_info(self) -> dict:
        """
        Zwraca informacje o załadowanym modelu
        
        Returns:
            Słownik z informacjami o modelu
        """
        if self.model is None:
            return {
                "loaded": False,
                "error": "No model loaded"
            }
        
        info = {
            "loaded": True,
            "version": self.model_version,
            "path": str(self.model_path),
            "type": type(self.model).__name__
        }
        
        if hasattr(self.model, 'n_estimators'):
            info['n_estimators'] = self.model.n_estimators
        
        if hasattr(self.model, 'max_depth'):
            info['max_depth'] = self.model.max_depth
        
        if hasattr(self.model, 'n_features_in_'):
            info['n_features'] = self.model.n_features_in_
        
        return info

model_loader = ModelLoader()
