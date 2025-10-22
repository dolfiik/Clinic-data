import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from typing import Dict, Any, Optional

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

class TriagePreprocessor:
    """
    Preprocessor dla danych pacjenta - przygotowuje dane dla modelu ML
    """
    
    def __init__(self, scaler_path: Optional[str] = None):
        """
        Inicjalizacja preprocessora
        
        Args:
            scaler_path: Ścieżka do zapisanego scalera (opcjonalne)
        """
        self.scaler = None
        self.scaler_path = scaler_path or str(Path(settings.MODEL_PATH) / 'scaler.pkl')
        
        self.numerical_features = [
            'wiek', 'tetno', 'cisnienie_skurczowe', 'cisnienie_rozkurczowe',
            'temperatura', 'saturacja', 'gcs', 'bol', 'czestotliwosc_oddechow',
            'czas_od_objawow_h'
        ]
        
        self.templates = [
            'zawał_STEMI', 'udar_ciężki', 'uraz_wielonarządowy',
            'zapalenie_płuc_ciężkie', 'zapalenie_wyrostka', 'silne_krwawienie',
            'złamanie_proste', 'infekcja_moczu', 'zaostrzenie_astmy',
            'ból_brzucha_łagodny', 'skręcenie_lekkie', 'migrena',
            'przeziębienie', 'kontrola', 'receptura'
        ]
        
        self.departments = [
            'SOR', 'Interna', 'Kardiologia', 'Chirurgia',
            'Ortopedia', 'Neurologia', 'Pediatria', 'Ginekologia'
        ]
        
        self._load_scaler()
    
    def _load_scaler(self):
        """Ładuje zapisany scaler"""
        try:
            scaler_path = Path(self.scaler_path)
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print(f"✓ Scaler załadowany z: {scaler_path}")
            else:
                print(f"⚠ Scaler nie znaleziony: {scaler_path}")
                print("  Model będzie działał bez skalowania (może obniżyć dokładność)")
        except Exception as e:
            print(f"⚠ Błąd ładowania scalera: {e}")
            self.scaler = None
    
    def _fill_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wypełnia brakujące wartości domyślnymi
        
        Args:
            data: Słownik z danymi pacjenta
            
        Returns:
            Dane z wypełnionymi wartościami
        """
        defaults = {
            'tetno': 75.0,
            'cisnienie_skurczowe': 120.0,
            'cisnienie_rozkurczowe': 80.0,
            'temperatura': 36.6,
            'saturacja': 98.0,
            'gcs': 15,
            'bol': 5,
            'czestotliwosc_oddechow': 16.0,
            'czas_od_objawow_h': 24.0
        }
        
        filled_data = data.copy()
        
        for feature, default_value in defaults.items():
            if feature not in filled_data or filled_data[feature] is None:
                filled_data[feature] = default_value
        
        return filled_data
    
    def _create_numerical_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Tworzy DataFrame z cechami numerycznymi
        
        Args:
            data: Słownik z danymi pacjenta
            
        Returns:
            DataFrame z cechami numerycznymi
        """
        data = self._fill_missing_values(data)
        numerical_data = {}
        
        for feature in self.numerical_features:
            if feature in data:
                value = data[feature]
                if value is not None:
                    numerical_data[feature] = float(value)
                else:
                    numerical_data[feature] = 0.0
            else:
                numerical_data[feature] = 0.0
        
        df = pd.DataFrame([numerical_data])
        
        return df
    
    def _one_hot_encode_template(self, template: Optional[str]) -> pd.DataFrame:
        """
        One-hot encoding dla szablonu przypadku
        
        Args:
            template: Nazwa szablonu przypadku
            
        Returns:
            DataFrame z kolumnami one-hot encoded
        """
        encoded = {}
        
        for t in self.templates:
            col_name = f'szablon_{t}'
            encoded[col_name] = 1 if template == t else 0
        
        return pd.DataFrame([encoded])
    
    def _one_hot_encode_gender(self, gender: str) -> pd.DataFrame:
        """
        One-hot encoding dla płci
        
        Args:
            gender: Płeć (M lub K)
            
        Returns:
            DataFrame z kolumnami one-hot encoded
        """
        encoded = {
            'plec_M': 1 if gender == 'M' else 0,
            'plec_K': 1 if gender == 'K' else 0
        }
        
        return pd.DataFrame([encoded])
    
    def _feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Tworzy dodatkowe cechy (feature engineering)
        
        Args:
            df: DataFrame z podstawowymi cechami
            
        Returns:
            DataFrame z dodatkowymi cechami
        """
        df_eng = df.copy()
        
        if 'cisnienie_skurczowe' in df.columns and 'cisnienie_rozkurczowe' in df.columns:
            df_eng['cisnienie_pulsowe'] = df['cisnienie_skurczowe'] - df['cisnienie_rozkurczowe']
        
        if 'cisnienie_skurczowe' in df.columns and 'cisnienie_rozkurczowe' in df.columns:
            df_eng['srednie_cisnienie'] = (df['cisnienie_skurczowe'] + 2 * df['cisnienie_rozkurczowe']) / 3
        
        if 'tetno' in df.columns and 'cisnienie_skurczowe' in df.columns:
            with np.errstate(divide='ignore', invalid='ignore'):
                shock_idx = df['tetno'] / df['cisnienie_skurczowe']
                df_eng['shock_index'] = np.where(np.isfinite(shock_idx), shock_idx, 0)
        
        if 'wiek' in df.columns:
            df_eng['wiek_dziecko'] = (df['wiek'] < 18).astype(float)
            df_eng['wiek_senior'] = (df['wiek'] > 65).astype(float)
        
        if 'temperatura' in df.columns:
            df_eng['goraczka'] = (df['temperatura'] > 38.0).astype(float)
            df_eng['goraczka_wysoka'] = (df['temperatura'] > 39.0).astype(float)
        
        if 'saturacja' in df.columns:
            df_eng['hipoksja'] = (df['saturacja'] < 90).astype(float)
            df_eng['hipoksja_ciezka'] = (df['saturacja'] < 85).astype(float)
        
        return df_eng
    
    def transform(self, patient_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Przetwarza dane pacjenta do formatu gotowego dla modelu
        
        Args:
            patient_data: Słownik z danymi pacjenta (surowe wartości)
            
        Returns:
            DataFrame gotowy do predykcji
        """
        df_numerical = self._create_numerical_dataframe(patient_data)
        
        df_engineered = self._feature_engineering(df_numerical)
        
        gender = patient_data.get('plec', 'M')
        df_gender = self._one_hot_encode_gender(gender)
        
        template = patient_data.get('szablon_przypadku', None)
        df_template = self._one_hot_encode_template(template)
        
        df_final = pd.concat([df_engineered, df_gender, df_template], axis=1)
        
        if self.scaler is not None:
            try:
                df_final = pd.DataFrame(
                    self.scaler.transform(df_final),
                    columns=df_final.columns
                )
            except Exception as e:
                print(f"⚠ Błąd skalowania: {e}")
                print("  Kontynuuję bez skalowania...")
        
        return df_final
    
    def get_feature_names(self) -> list:
        """
        Zwraca listę wszystkich nazw cech po preprocessingu
        
        Returns:
            Lista nazw cech
        """
        features = []
        
        features.extend(self.numerical_features)
        
        features.extend([
            'cisnienie_pulsowe', 'srednie_cisnienie', 'shock_index',
            'wiek_dziecko', 'wiek_senior',
            'goraczka', 'goraczka_wysoka',
            'hipoksja', 'hipoksja_ciezka'
        ])
        
        features.extend(['plec_M', 'plec_K'])
        
        features.extend([f'szablon_{t}' for t in self.templates])
        
        return features
    
    def validate_input(self, patient_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Waliduje dane wejściowe
        
        Args:
            patient_data: Dane pacjenta
            
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['wiek', 'plec']
        
        for field in required_fields:
            if field not in patient_data or patient_data[field] is None:
                return False, f"Missing required field: {field}"
        
        if patient_data['wiek'] < 0 or patient_data['wiek'] > 120:
            return False, "Age must be between 0 and 120"
        
        if patient_data['plec'] not in ['M', 'K']:
            return False, "Gender must be 'M' or 'K'"
        
        ranges = {
            'tetno': (0, 300),
            'cisnienie_skurczowe': (0, 300),
            'cisnienie_rozkurczowe': (0, 200),
            'temperatura': (30, 45),
            'saturacja': (0, 100),
            'gcs': (3, 15),
            'bol': (0, 10),
            'czestotliwosc_oddechow': (0, 100)
        }
        
        for field, (min_val, max_val) in ranges.items():
            if field in patient_data and patient_data[field] is not None:
                value = float(patient_data[field])
                if value < min_val or value > max_val:
                    return False, f"{field} must be between {min_val} and {max_val}"
        
        return True, None

preprocessor = TriagePreprocessor()
