import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from typing import Dict, Any, Optional
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

class TriagePreprocessor:
    """
    Preprocessor dla danych pacjenta - przygotowuje dane dla modelu ML
    """
    
    def __init__(self, scaler_path: Optional[str] = None):
        """Inicjalizacja preprocessora"""
        self.scaler = None
        self.scaler_path = scaler_path or str(Path(settings.MODEL_PATH) / 'scaler.pkl')
        
        self.numerical_features = [
            'wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
            'temperatura', 'saturacja'
        ]
        
        self.templates = [
            'ból_brzucha_łagodny',      
            'infekcja_moczu',           
            'kontrola',
            'migrena',
            'przeziębienie',
            'receptura',
            'silne_krwawienie',
            'skręcenie_lekkie',
            'udar_ciężki',              
            'uraz_wielonarządowy',
            'zaostrzenie_astmy',
            'zapalenie_płuc_ciężkie',   
            'zapalenie_wyrostka',
            'zawał_STEMI',              
            'złamanie_proste'           
        ]
        
        self.departments = [
            'Chirurgia', 'Interna', 'Kardiologia', 
            'Neurologia', 'Ortopedia', 'SOR'
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
                print("  Model będzie działał bez skalowania")
                self.scaler = None  
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
            'tętno': 75.0,
            'ciśnienie_skurczowe': 120.0,
            'ciśnienie_rozkurczowe': 80.0,
            'temperatura': 36.6,
            'saturacja': 98.0
        }
        
        filled_data = data.copy()
        
        for feature, default_value in defaults.items():
            if feature not in filled_data or filled_data[feature] is None:
                filled_data[feature] = default_value
        
        return filled_data
    
    def _normalize_template_name(self, template: Optional[str]) -> Optional[str]:
        """
        Normalizuje nazwę szablonu do formatu oczekiwanego przez model
        
        Args:
            template: Oryginalna nazwa szablonu
            
        Returns:
            Znormalizowana nazwa lub None
        """
        if not template:
            return None
        
        template_mapping = {
            'Ból brzucha': 'ból_brzucha_łagodny',
            'Ból w klatce piersiowej': 'zawał_STEMI',
            'bol_w_klatce': 'zawał_STEMI',
            'bol_brzucha': 'ból_brzucha_łagodny',
            'infekcja_ukladu_moczowego': 'infekcja_moczu',
            'udar': 'udar_ciężki',
            'zapalenie_pluc': 'zapalenie_płuc_ciężkie',
            'zlamanie_konczyny': 'złamanie_proste',
            'migrena': 'migrena',
            'silne_krwawienie': 'silne_krwawienie',
            'zaostrzenie_astmy': 'zaostrzenie_astmy',
            'zapalenie_wyrostka': 'zapalenie_wyrostka',
            'uraz_wielonarzadowy': 'uraz_wielonarządowy'
        }        
        if template in template_mapping:
            return template_mapping[template]
        
        normalized = template.lower().replace(' ', '_').replace('ł', 'l').replace('ą', 'a').replace('ę', 'e').replace('ć', 'c').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
        
        if normalized in self.templates:
            return normalized
        
        return None
    
    def _create_numerical_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Tworzy DataFrame z cechami numerycznymi
        
        Args:
            data: Słownik z danymi pacjenta
            
        Returns:
            DataFrame z cechami numerycznymi
        """
        field_mapping = {
        'tetno': 'tętno',
        'cisnienie_skurczowe': 'ciśnienie_skurczowe',
        'cisnienie_rozkurczowe': 'ciśnienie_rozkurczowe',
        'bol': 'ból',
        'czestotliwosc_oddechow': 'częstotliwość_oddechów',
        'czas_od_objawow_h': 'czas_od_objawów_h'
        }
        
        normalized_data = {}
        for key, value in data.items():
            new_key = field_mapping.get(key, key)
            normalized_data[new_key] = value
        
        normalized_data = self._fill_missing_values(normalized_data)
        numerical_data = {}
        
        for feature in self.numerical_features:
            if feature in normalized_data:
                value = normalized_data[feature]
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
        normalized_template = self._normalize_template_name(template)
        
        encoded = {}
        
        for t in self.templates:
            col_name = f'szablon_{t}'
            encoded[col_name] = 1 if normalized_template == t else 0
        
        return pd.DataFrame([encoded])
    
    def _one_hot_encode_gender(self, gender: str) -> pd.DataFrame:
        """
        One-hot encoding dla płci - JEDNA kolumna jak w modelu
        
        Args:
            gender: Płeć (M lub K)
            
        Returns:
            DataFrame z jedną kolumną płeć_encoded
        """
        encoded = {
            'płeć_encoded': 1 if gender == 'M' else 0
        }
        
        return pd.DataFrame([encoded])
    
    def _add_datetime_features(self) -> pd.DataFrame:
        """
        Dodaje cechy związane z czasem (godzina, dzień tygodnia, etc.)
        
        Returns:
            DataFrame z cechami czasowymi
        """
        now = datetime.now()
        
        datetime_features = {
            'godzina': now.hour,
            'dzien_tygodnia': now.weekday(),
            'miesiac': now.month,
            'czy_weekend': 1 if now.weekday() >= 5 else 0
        }
        
        return pd.DataFrame([datetime_features])
    
    def _one_hot_encode_departments(self) -> pd.DataFrame:
        """
        One-hot encoding dla oddziałów - wszystkie na 0 (nie znamy jeszcze oddziału docelowego)
        
        Returns:
            DataFrame z kolumnami one-hot encoded dla oddziałów
        """
        encoded = {}
        
        for dept in self.departments:
            col_name = f'oddział_{dept}'
            encoded[col_name] = 0
        
        return pd.DataFrame([encoded])
    
    def transform(self, patient_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Przetwarza dane pacjenta do formatu gotowego dla modelu
        
        Args:
            patient_data: Słownik z danymi pacjenta (surowe wartości)
            
        Returns:
            DataFrame gotowy do predykcji
        """
        df_numerical = self._create_numerical_dataframe(patient_data)
        
        gender = patient_data.get('plec', 'M')
        df_gender = self._one_hot_encode_gender(gender)
        
        df_datetime = self._add_datetime_features()
        
        df_departments = self._one_hot_encode_departments()
        
        template = patient_data.get('szablon_przypadku', None)
        df_template = self._one_hot_encode_template(template)
        
        # ✅ Kolejność MUSI być zgodna z modelem!
        df_final = pd.concat([
            df_numerical,      # wiek, tętno, ciśnienie_skurczowe, ciśnienie_rozkurczowe, temperatura, saturacja
            df_gender,         # płeć_encoded
            df_datetime,       # godzina, dzien_tygodnia, miesiac, czy_weekend
            df_departments,    # oddział_*
            df_template        # szablon_*
        ], axis=1)
        
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
        
        # Numerical
        features.extend(self.numerical_features)
        
        # Gender
        features.append('płeć_encoded')
        
        # Datetime
        features.extend(['godzina', 'dzien_tygodnia', 'miesiac', 'czy_weekend'])
        
        # Departments
        features.extend([f'oddział_{d}' for d in self.departments])
        
        # Templates
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
            'saturacja': (0, 100)
        }
        
        for field, (min_val, max_val) in ranges.items():
            if field in patient_data and patient_data[field] is not None:
                value = float(patient_data[field])
                if value < min_val or value > max_val:
                    return False, f"{field} must be between {min_val} and {max_val}"
        
        return True, None

preprocessor = TriagePreprocessor()
