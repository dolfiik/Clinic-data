import pickle
from pathlib import Path
from app.core.config import settings

class ModelLoader:
    """Klasa do ładowania modeli ML"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
    
    def load_latest_model(self):
        """Ładuje najnowszy model z folderu models/"""
        model_path = Path(settings.MODEL_PATH)
        
        # Znajdź najnowszy model
        models = list(model_path.glob("random_forest_*.pkl"))
        if not models:
            raise FileNotFoundError("Nie znaleziono żadnych modeli")
        
        latest_model = max(models, key=lambda p: p.stat().st_mtime)
        
        with open(latest_model, 'rb') as f:
            self.model = pickle.load(f)
        
        return self.model
    
    def load_scaler(self):
        """Ładuje scaler"""
        scaler_path = Path(settings.SCALER_PATH)
        
        if not scaler_path.exists():
            raise FileNotFoundError(f"Nie znaleziono scalera: {scaler_path}")
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        return self.scaler

# Singleton
model_loader = ModelLoader()
