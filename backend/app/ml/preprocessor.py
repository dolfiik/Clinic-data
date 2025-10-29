import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

class TriagePreprocessor:
    """
    Preprocessor dla modelu BEZ SKALOWANIA (26 cech)
    Dopasowany do: random_forest_no_scaling_20251029_095044.pkl
    """
    
    def __init__(self):
        """Inicjalizacja preprocessora"""
        
        # ✅ 10 cech numerycznych - DOKŁADNIE jak w modelu
        self.numerical_features = [
            'wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
            'temperatura', 'saturacja', 'GCS', 'ból', 
            'częstotliwość_oddechów', 'czas_od_objawów_h'
        ]
        
        # ✅ 15 szablonów - DOKŁADNIE jak w modelu
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
        
        print("✓ Preprocessor zainicjalizowany (26 cech, BEZ skalowania)")
    
    def _fill_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Uzupełnia brakujące wartości domyślnymi"""
        defaults = {
            'wiek': 50,
            'tętno': 75.0,
            'ciśnienie_skurczowe': 120.0,
            'ciśnienie_rozkurczowe': 80.0,
            'temperatura': 36.6,
            'saturacja': 98.0,
            'GCS': 15,
            'ból': 0,
            'częstotliwość_oddechów': 16.0,
            'czas_od_objawów_h': 1.0
        }
        
        filled_data = data.copy()
        for key, default_value in defaults.items():
            if key not in filled_data or filled_data[key] is None:
                filled_data[key] = default_value
        
        return filled_data
    
    def _normalize_template_name(self, template: Optional[str]) -> Optional[str]:
        """
        Normalizuje nazwy szablonów do formatu oczekiwanego przez model
        """
        if not template:
            return None
        
        # ✅ Mapowanie różnych wariantów
        template_mapping = {
            # Dokładne dopasowania
            'zawał_STEMI': 'zawał_STEMI',
            'ból_brzucha_łagodny': 'ból_brzucha_łagodny',
            'infekcja_moczu': 'infekcja_moczu',
            'udar_ciężki': 'udar_ciężki',
            'zapalenie_płuc_ciężkie': 'zapalenie_płuc_ciężkie',
            'złamanie_proste': 'złamanie_proste',
            'uraz_wielonarządowy': 'uraz_wielonarządowy',
            'przeziębienie': 'przeziębienie',
            'kontrola': 'kontrola',
            'receptura': 'receptura',
            'skręcenie_lekkie': 'skręcenie_lekkie',
            'migrena': 'migrena',
            'silne_krwawienie': 'silne_krwawienie',
            'zaostrzenie_astmy': 'zaostrzenie_astmy',
            'zapalenie_wyrostka': 'zapalenie_wyrostka',
            
            # Bez polskich znaków -> z polskimi
            'zawal_STEMI': 'zawał_STEMI',
            'zawal_stemi': 'zawał_STEMI',
            'bol_brzucha_lagodny': 'ból_brzucha_łagodny',
            'bol_brzucha': 'ból_brzucha_łagodny',
            'udar_ciezki': 'udar_ciężki',
            'udar': 'udar_ciężki',
            'zapalenie_pluc_ciezkie': 'zapalenie_płuc_ciężkie',
            'zapalenie_pluc': 'zapalenie_płuc_ciężkie',
            'zlamanie_proste': 'złamanie_proste',
            'uraz_wielonarzadowy': 'uraz_wielonarządowy',
            'przeziebienie': 'przeziębienie',
            'skrecenie_lekkie': 'skręcenie_lekkie',
            
            # Alternatywne nazwy
            'zawał': 'zawał_STEMI',
            'udar mózgu': 'udar_ciężki',
            'zapalenie płuc': 'zapalenie_płuc_ciężkie',
            'złamanie': 'złamanie_proste',
            'krwawienie': 'silne_krwawienie',
            'astma': 'zaostrzenie_astmy',
            'wyrostek': 'zapalenie_wyrostka',
        }
        
        # Spróbuj mapowania
        if template in template_mapping:
            mapped = template_mapping[template]
            print(f"  📝 Mapowanie: '{template}' → '{mapped}'")
            return mapped
        
        # Sprawdź czy nazwa jest już poprawna
        if template in self.templates:
            print(f"  ✓ Szablon OK: '{template}'")
            return template
        
        # Jeśli nie znaleziono
        print(f"  ⚠ NIEZNANY szablon: '{template}'")
        print(f"    Model będzie decydował TYLKO na parametrach życiowych!")
        return None
    
    def _create_numerical_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Tworzy DataFrame z cechami numerycznymi (10 cech)
        """
        # Mapowanie nazw z bazy na nazwy preprocessingu
        field_mapping = {
            'tetno': 'tętno',
            'cisnienie_skurczowe': 'ciśnienie_skurczowe',
            'cisnienie_rozkurczowe': 'ciśnienie_rozkurczowe',
            'gcs': 'GCS',
            'bol': 'ból',
            'czestotliwosc_oddechow': 'częstotliwość_oddechów',
            'czas_od_objawow_h': 'czas_od_objawów_h'
        }
        
        # Przekształć klucze
        normalized_data = {}
        for key, value in data.items():
            new_key = field_mapping.get(key, key)
            normalized_data[new_key] = value
        
        # Uzupełnij brakujące
        normalized_data = self._fill_missing_values(normalized_data)
        
        # Wybierz tylko cechy numeryczne
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
    
    def _one_hot_encode_gender(self, gender: str) -> pd.DataFrame:
        """
        One-hot encoding dla płci - JEDNA kolumna płeć_M
        
        Args:
            gender: Płeć (M lub K)
            
        Returns:
            DataFrame z jedną kolumną płeć_M (1 jeśli M, 0 jeśli K)
        """
        encoded = {
            'płeć_M': 1 if gender == 'M' else 0
        }
        
        return pd.DataFrame([encoded])
    
    def _one_hot_encode_template(self, template: Optional[str]) -> pd.DataFrame:
        """
        One-hot encoding dla szablonu przypadku (15 kolumn)
        
        Args:
            template: Nazwa szablonu przypadku
            
        Returns:
            DataFrame z 15 kolumnami szablon_*
        """
        normalized_template = self._normalize_template_name(template)
        
        encoded = {}
        
        for t in self.templates:
            col_name = f'szablon_{t}'
            encoded[col_name] = 1 if normalized_template == t else 0
        
        return pd.DataFrame([encoded])
    
    def transform(self, patient_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Przetwarza dane pacjenta do formatu gotowego dla modelu
        
        Args:
            patient_data: Słownik z danymi pacjenta (surowe wartości)
            
        Returns:
            DataFrame gotowy do predykcji (26 cech)
        """
        # 1. Cechy numeryczne (10 kolumn)
        df_numerical = self._create_numerical_dataframe(patient_data)
        
        # 2. Płeć (1 kolumna: płeć_M)
        gender = patient_data.get('plec', 'M')
        df_gender = self._one_hot_encode_gender(gender)
        
        # 3. Szablon (15 kolumn: szablon_*)
        template = patient_data.get('szablon_przypadku', None)
        df_template = self._one_hot_encode_template(template)
        
        # ✅ KOLEJNOŚĆ ZGODNA Z MODELEM!
        # 10 numerical + 1 gender + 15 templates = 26 cech
        df_final = pd.concat([
            df_numerical,   # wiek, tętno, ..., czas_od_objawów_h
            df_gender,      # płeć_M
            df_template     # szablon_*
        ], axis=1)
        
        # ✅ BRAK SKALOWANIA - model trenowany na surowych wartościach!
        print(f"✓ Preprocessing zakończony: {df_final.shape[1]} cech (BEZ skalowania)")
        
        return df_final
    
    def get_feature_names(self) -> list:
        """
        Zwraca listę wszystkich nazw cech po preprocessingu
        
        Returns:
            Lista 26 nazw cech
        """
        features = []
        
        # Numerical (10)
        features.extend(self.numerical_features)
        
        # Gender (1)
        features.append('płeć_M')
        
        # Templates (15)
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
            'bol': (0, 10)
        }
        
        for field, (min_val, max_val) in ranges.items():
            if field in patient_data and patient_data[field] is not None:
                value = float(patient_data[field])
                if value < min_val or value > max_val:
                    return False, f"{field} must be between {min_val} and {max_val}"
        
        return True, None

# Singleton instance
preprocessor = TriagePreprocessor()
