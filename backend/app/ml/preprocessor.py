import sys
from pathlib import Path
import pandas as pd

# Dodaj główny projekt do path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class TriagePreprocessor:
    """
    Wrapper na preprocessing z src/preprocessing/preprocess_data.py
    """
    
    def __init__(self):
        # TODO: Zaimportować i użyć Twojego preprocessingu
        pass
    
    def transform(self, patient_data: dict) -> pd.DataFrame:
        """
        Przetwarza dane pacjenta do formatu gotowego dla modelu
        
        Args:
            patient_data: Słownik z danymi pacjenta (surowe wartości)
        
        Returns:
            DataFrame gotowy do predykcji
        """
        # TODO: Implementacja używająca src/preprocessing
        pass

preprocessor = TriagePreprocessor()
