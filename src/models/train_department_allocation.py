import pandas as pd
import numpy as np
import json
import pickle
import warnings
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, balanced_accuracy_score
)

import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier

import tensorflow as tf
from tensorflow import keras

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# KONFIGURACJA
# ============================================================================

DATA_PATH = Path('data/raw/')
MODEL_PATH = Path('models/')
RESULTS_PATH = Path('results/')

RESULTS_PATH.mkdir(parents=True, exist_ok=True)

MODEL_VERSION = "3.0.0"
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# LSTM Model 2 był trenowany na 8 oddziałach - musimy używać tej samej listy dla LSTM
DEPARTMENTS_FULL = ["SOR", "Interna", "Kardiologia", "Chirurgia", 
                    "Ortopedia", "Neurologia", "Pediatria", "Ginekologia"]

# Ale dla Model 3 trenujemy tylko na 6 oddziałach (bez Pediatria/Ginekologia - class imbalance)
DEPARTMENTS = ["SOR", "Interna", "Kardiologia", "Chirurgia", 
               "Ortopedia", "Neurologia"]

DEPARTMENT_CAPACITY_FULL = {
    "SOR": 25, "Interna": 50, "Kardiologia": 30, "Chirurgia": 35,
    "Ortopedia": 25, "Neurologia": 20, "Pediatria": 30, "Ginekologia": 20
}

DEPARTMENT_CAPACITY = {
    "SOR": 25, "Interna": 50, "Kardiologia": 30, "Chirurgia": 35,
    "Ortopedia": 25, "Neurologia": 20
}

# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def print_header(text: str):
    """Wyświetla sformatowany nagłówek"""
    logger.info("\n" + "="*70)
    logger.info(f" {text}")
    logger.info("="*70)


def load_latest_lstm_model():
    """
    Wczytuje najnowszy model LSTM z latest_model.json
    
    Returns:
        Tuple: (model, scalers, metadata)
    """
    logger.info("\n🔵 Wczytywanie najnowszego LSTM Model 2...")
    
    # Wczytaj info o latest model
    latest_info_path = MODEL_PATH / 'latest_model.json'
    
    if not latest_info_path.exists():
        raise FileNotFoundError(
            "Nie znaleziono latest_model.json. Najpierw wytrenuj Model 2!"
        )
    
    with open(latest_info_path, 'r') as f:
        latest_info = json.load(f)
    
    model_path = Path(latest_info['model_path'])
    scalers_path = Path(latest_info['scalers_path'])
    metadata_path = Path(latest_info['metadata_path'])
    
    logger.info(f"  Model version: {latest_info['version']}")
    logger.info(f"  MAE: {latest_info['mae']:.2f}")
    
    # Load model
    lstm_model = keras.models.load_model(model_path)
    logger.info(f"  ✓ Model: {model_path.name}")
    
    # Load scalers
    with open(scalers_path, 'rb') as f:
        lstm_scalers = pickle.load(f)
    logger.info(f"  ✓ Scalers: {scalers_path.name}")
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        lstm_metadata = json.load(f)
    logger.info(f"  ✓ Metadata: lookback={lstm_metadata['lookback_hours']}h, "
                f"horizon={lstm_metadata['prediction_horizon']}h")
    
    return lstm_model, lstm_scalers, lstm_metadata


# ============================================================================
# 1. WCZYTANIE DANYCH
# ============================================================================

def load_data():
    """Wczytuje dane arrangement i triage"""
    print_header("Wczytywanie danych")
    
    # Arrangement data
    df_arr = pd.read_csv(DATA_PATH / 'department_arrangement_data.csv')
    logger.info(f"✓ Arrangement data: {len(df_arr)} rekordów")
    
    # Triage data
    df_triage = pd.read_csv(DATA_PATH / 'triage_data.csv')
    logger.info(f"✓ Triage data: {len(df_triage)} rekordów")
    
    # Parse timestamp
    df_arr['timestamp'] = pd.to_datetime(df_arr['timestamp'])
    df_arr = df_arr.sort_values('timestamp').reset_index(drop=True)
    
    # Parse JSON obłożenia
    occupancy_data = []
    for idx, row in df_arr.iterrows():
        occ_dict = json.loads(row['obłożenie_oddziałów'])
        occupancy_data.append(occ_dict)
    
    df_occ = pd.DataFrame(occupancy_data)
    
    # Dodaj obłożenie do df_arr - WSZYSTKIE 8 oddziałów (potrzebne dla LSTM)
    for dept in DEPARTMENTS_FULL:
        df_arr[f'occ_{dept}'] = df_occ[dept]
        df_arr[f'occ_pct_{dept}'] = df_occ[dept] / DEPARTMENT_CAPACITY_FULL[dept]
    
    logger.info(f"\n✓ Dane przetworzone: {df_arr.shape}")
    logger.info(f"  Używamy wszystkich {len(DEPARTMENTS_FULL)} oddziałów dla LSTM compatibility")
    
    return df_arr, df_triage


# ============================================================================
# 2. PREPARE LSTM SEQUENCES
# ============================================================================

def prepare_lstm_sequences(
    df_arr: pd.DataFrame,
    lstm_metadata: Dict
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Przygotowuje sekwencje dla LSTM prediction
    
    Args:
        df_arr: DataFrame z danymi arrangement
        lstm_metadata: Metadata z LSTM modelu
        
    Returns:
        X_seq: (n_samples, lookback, n_features) - sekwencje
        X_static: (n_samples, n_static_features) - cechy statyczne
        df_valid: DataFrame tylko z valid samples (po lookback)
    """
    print_header("Przygotowanie sekwencji dla LSTM")
    
    lookback = lstm_metadata['lookback_hours']
    
    logger.info(f"\n📊 Budowanie sekwencji (lookback={lookback}h)...")
    
    # Cechy czasowe
    df_arr['hour'] = df_arr['timestamp'].dt.hour
    df_arr['day_of_week'] = df_arr['timestamp'].dt.dayofweek
    df_arr['month'] = df_arr['timestamp'].dt.month
    df_arr['day_of_month'] = df_arr['timestamp'].dt.day
    df_arr['is_weekend'] = (df_arr['day_of_week'] >= 5).astype(int)
    df_arr['is_night'] = ((df_arr['hour'] < 6) | (df_arr['hour'] >= 22)).astype(int)
    df_arr['is_peak_hours'] = ((df_arr['hour'] >= 8) & (df_arr['hour'] <= 20)).astype(int)
    
    # Cyclical encoding
    df_arr['hour_sin'] = np.sin(2 * np.pi * df_arr['hour'] / 24)
    df_arr['hour_cos'] = np.cos(2 * np.pi * df_arr['hour'] / 24)
    df_arr['day_sin'] = np.sin(2 * np.pi * df_arr['day_of_week'] / 7)
    df_arr['day_cos'] = np.cos(2 * np.pi * df_arr['day_of_week'] / 7)
    
    # Agregaty (7d, 30d)
    logger.info("  Obliczanie agregatów...")
    for dept in DEPARTMENTS_FULL:  # Używamy FULL dla LSTM
        # Rolling averages już mogą istnieć, ale przeliczymy dla pewności
        df_arr[f'{dept}_avg_7d'] = df_arr[f'occ_{dept}'].rolling(
            window=168, min_periods=24
        ).mean().fillna(df_arr[f'occ_{dept}'].mean())
        
        df_arr[f'{dept}_avg_30d'] = df_arr[f'occ_{dept}'].rolling(
            window=720, min_periods=24
        ).mean().fillna(df_arr[f'occ_{dept}'].mean())
        
        df_arr[f'{dept}_std_7d'] = df_arr[f'occ_{dept}'].rolling(
            window=168, min_periods=24
        ).std().fillna(df_arr[f'occ_{dept}'].std())
        
        df_arr[f'{dept}_trend_24h'] = df_arr[f'occ_{dept}'].diff(24).fillna(0)
        
        # Capacity ratio - używamy occ_pct jeśli istnieje, lub tworzymy
        if f'occ_pct_{dept}' not in df_arr.columns:
            df_arr[f'occ_pct_{dept}'] = df_arr[f'occ_{dept}'] / DEPARTMENT_CAPACITY_FULL[dept]
        df_arr[f'{dept}_capacity_ratio'] = df_arr[f'occ_pct_{dept}']
    
    # Buduj sekwencje - używamy DEPARTMENTS_FULL (8 oddziałów) dla LSTM
    seq_columns = [f'occ_{dept}' for dept in DEPARTMENTS_FULL] + [f'{dept}_capacity_ratio' for dept in DEPARTMENTS_FULL]
    
    static_columns = [
        'hour', 'day_of_week', 'month', 'day_of_month',
        'is_weekend', 'is_night', 'is_peak_hours',
        'hour_sin', 'hour_cos', 'day_sin', 'day_cos'
    ]
    
    for dept in DEPARTMENTS_FULL:  # Używamy FULL dla LSTM
        static_columns.extend([
            f'{dept}_avg_7d', f'{dept}_avg_30d',
            f'{dept}_std_7d', f'{dept}_trend_24h'
        ])
    
    X_seq_list = []
    X_static_list = []
    valid_indices = []
    
    logger.info(f"  Tworzenie {len(df_arr) - lookback} sekwencji...")
    
    for i in range(lookback, len(df_arr)):
        # Sekwencja (lookback hours)
        seq = df_arr[seq_columns].iloc[i-lookback:i].values
        X_seq_list.append(seq)
        
        # Static features (current timestamp)
        static = df_arr[static_columns].iloc[i].values
        X_static_list.append(static)
        
        valid_indices.append(i)
        
        if (i - lookback) % 500 == 0:
            progress = (i - lookback) / (len(df_arr) - lookback) * 100
            print(f"  Postęp: {progress:.1f}%", end='\r')
    
    X_seq = np.array(X_seq_list)
    X_static = np.array(X_static_list)
    df_valid = df_arr.iloc[valid_indices].reset_index(drop=True)
    
    logger.info(f"\n✓ Utworzono sekwencje")
    logger.info(f"  X_seq shape:    {X_seq.shape}")
    logger.info(f"  X_static shape: {X_static.shape}")
    logger.info(f"  Valid samples:  {len(df_valid)}")
    logger.info(f"  Pominięto pierwszych {lookback}h (cold start)")
    
    return X_seq, X_static, df_valid


# ============================================================================
# 3. LSTM PREDICTIONS (BATCH)
# ============================================================================

def predict_future_occupancy_batch(
    X_seq: np.ndarray,
    X_static: np.ndarray,
    lstm_model: keras.Model,
    lstm_scalers: Dict,
    batch_size: int = 256
) -> np.ndarray:
    """
    Wykonuje batch prediction na LSTM
    
    Args:
        X_seq: Sekwencje (n_samples, lookback, n_features)
        X_static: Static features (n_samples, n_static)
        lstm_model: Wytrenowany model LSTM
        lstm_scalers: Dict ze scalerami
        batch_size: Rozmiar batcha
        
    Returns:
        predictions: (n_samples, n_departments) - predicted occupancy
    """
    print_header("LSTM Batch Prediction")
    
    seq_scaler = lstm_scalers['seq_scaler']
    static_scaler = lstm_scalers['static_scaler']
    target_scaler = lstm_scalers['target_scaler']
    
    # Diagnostyka
    logger.info(f"\n🔍 Diagnostyka features:")
    logger.info(f"  X_seq shape: {X_seq.shape}")
    logger.info(f"  X_static shape: {X_static.shape}")
    
    # Sprawdź ile features oczekuje scaler
    if hasattr(seq_scaler, 'n_features_in_'):
        logger.info(f"  seq_scaler expects: {seq_scaler.n_features_in_} features")
        logger.info(f"  X_seq has: {X_seq.shape[2]} features")
        
        if X_seq.shape[2] != seq_scaler.n_features_in_:
            logger.error(f"  ❌ MISMATCH! Scaler expects {seq_scaler.n_features_in_}, got {X_seq.shape[2]}")
            raise ValueError(f"Feature count mismatch: expected {seq_scaler.n_features_in_}, got {X_seq.shape[2]}")
    
    if hasattr(static_scaler, 'n_features_in_'):
        logger.info(f"  static_scaler expects: {static_scaler.n_features_in_} features")
        logger.info(f"  X_static has: {X_static.shape[1]} features")
        
        if X_static.shape[1] != static_scaler.n_features_in_:
            logger.error(f"  ❌ MISMATCH! Scaler expects {static_scaler.n_features_in_}, got {X_static.shape[1]}")
            raise ValueError(f"Feature count mismatch: expected {static_scaler.n_features_in_}, got {X_static.shape[1]}")
    
    logger.info(f"\n🔮 Normalizacja danych...")
    
    # Normalizuj sekwencje
    n_samples, lookback, n_seq_features = X_seq.shape
    X_seq_scaled = seq_scaler.transform(
        X_seq.reshape(-1, n_seq_features)
    ).reshape(n_samples, lookback, n_seq_features)
    
    # Normalizuj static
    X_static_scaled = static_scaler.transform(X_static)
    
    logger.info(f"✓ Dane znormalizowane")
    logger.info(f"\n🚀 Predykcja w batchach (batch_size={batch_size})...")
    
    # Batch prediction
    predictions_scaled = lstm_model.predict(
        [X_seq_scaled, X_static_scaled],
        batch_size=batch_size,
        verbose=1
    )
    
    # Denormalizacja
    predictions = target_scaler.inverse_transform(predictions_scaled)
    
    # Clip do sensownych wartości
    for i, dept in enumerate(DEPARTMENTS):
        predictions[:, i] = np.clip(
            predictions[:, i], 
            0, 
            DEPARTMENT_CAPACITY[dept] * 1.2
        )
    
    logger.info(f"\n✓ Predykcje gotowe: {predictions.shape}")
    logger.info(f"  (Predictions dla wszystkich {len(DEPARTMENTS_FULL)} oddziałów)")
    logger.info(f"\n📊 Statystyki predykcji:")
    
    for i, dept in enumerate(DEPARTMENTS_FULL):
        mean_pred = predictions[:, i].mean()
        std_pred = predictions[:, i].std()
        logger.info(f"  {dept}: mean={mean_pred:.1f}, std={std_pred:.1f}")
    
    return predictions


# ============================================================================
# 4. FEATURE ENGINEERING
# ============================================================================

def create_features(
    df_arr: pd.DataFrame,
    df_triage: pd.DataFrame,
    future_occupancy: np.ndarray
) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Tworzy kompleksowy zestaw cech dla modelu alokacji
    
    Args:
        df_arr: DataFrame arrangement (już po LSTM predictions)
        df_triage: DataFrame triage
        future_occupancy: Predykcje z LSTM (n_samples, n_departments)
        
    Returns:
        X: Features
        y: Target (optymalne_przypisanie)
        feature_columns: Lista nazw cech
    """
    print_header("Feature Engineering dla Model 3")
    
    logger.info("\n📊 Merge z danymi triage...")
    
    # Merge
    df = df_arr.merge(
        df_triage,
        left_on='id_pacjenta',
        right_on='id_przypadku',
        how='left',
        suffixes=('', '_triage')
    )
    
    logger.info(f"  ✓ Połączono: {df.shape}")
    
    # ========================================================================
    # CECHY PACJENTA
    # ========================================================================
    
    logger.info("\n👤 Cechy pacjenta...")
    
    patient_features = [
        'wiek', 'płeć', 'kategoria_triażu',
        'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
        'temperatura', 'saturacja', 'GCS', 'ból',
        'częstotliwość_oddechów', 'czas_od_objawów_h'
    ]
    
    # Encode płeć
    df['płeć_encoded'] = (df['płeć'] == 'M').astype(int)
    
    # One-hot encode szablon
    szablon_dummies = pd.get_dummies(df['szablon_przypadku'], prefix='szablon')
    
    # ========================================================================
    # OBECNE OBCIĄŻENIE
    # ========================================================================
    
    logger.info("🏥 Obecne obciążenie oddziałów...")
    
    occupancy_features = []
    for dept in DEPARTMENTS:
        occupancy_features.extend([
            f'occ_{dept}',
            f'occ_pct_{dept}'
        ])
        
        # Overcrowded flag
        df[f'overcrowded_{dept}'] = (df[f'occ_pct_{dept}'] > 0.8).astype(int)
        occupancy_features.append(f'overcrowded_{dept}')
    
    # ========================================================================
    # PRZYSZŁE OBCIĄŻENIE (Z LSTM!)
    # ========================================================================
    
    logger.info("🔮 Przyszłe obciążenie (predykcje LSTM)...")
    
    # LSTM zwraca predictions dla wszystkich 8 oddziałów
    # Ale my trenujemy Model 3 tylko na 6 oddziałach (bez Pediatria/Ginekologia)
    
    # Mapowanie: który indeks w DEPARTMENTS_FULL odpowiada któremu w DEPARTMENTS
    dept_indices = {dept: i for i, dept in enumerate(DEPARTMENTS_FULL)}
    
    logger.info(f"  Filtrowanie z {len(DEPARTMENTS_FULL)} → {len(DEPARTMENTS)} oddziałów")
    logger.info(f"  Pomijam: Pediatria, Ginekologia (class imbalance)")
    
    for dept in DEPARTMENTS:  # Tylko 6 oddziałów
        full_idx = dept_indices[dept]  # Znajdź indeks w DEPARTMENTS_FULL
        df[f'future_occ_{dept}'] = future_occupancy[:, full_idx].round().astype(int)
        df[f'future_occ_pct_{dept}'] = df[f'future_occ_{dept}'] / DEPARTMENT_CAPACITY[dept]
        df[f'delta_occ_{dept}'] = df[f'future_occ_{dept}'] - df[f'occ_{dept}']
    
    # ========================================================================
    # KOMPATYBILNOŚĆ MEDYCZNA
    # ========================================================================
    
    logger.info("🩺 Kompatybilność medyczna...")
    
    # Mapowanie szablon → oddziały
    szablon_to_depts = {
        'ból w klatce piersiowej': ['Kardiologia', 'SOR'],
        'zaostrzenie astmy': ['Interna', 'SOR'],
        'uraz głowy': ['Neurologia', 'SOR', 'Chirurgia'],
        'złamanie kończyny': ['Ortopedia', 'SOR'],
        'udar': ['Neurologia', 'SOR'],
        'zaburzenia rytmu serca': ['Kardiologia', 'SOR'],
        'zapalenie płuc': ['Interna', 'SOR'],
        'zapalenie wyrostka': ['Chirurgia', 'SOR'],
        'silne krwawienie': ['Chirurgia', 'SOR'],
        'krwawienie z przewodu pokarmowego': ['Chirurgia', 'Interna'],
        'napad padaczkowy': ['Neurologia', 'SOR'],
        'omdlenie': ['Kardiologia', 'Neurologia', 'SOR'],
        'ból brzucha': ['Chirurgia', 'Interna', 'Ginekologia'],
        'reakcja alergiczna': ['Interna', 'SOR'],
        'migrena': ['Neurologia', 'SOR'],
        'zatrucie pokarmowe': ['Interna', 'SOR'],
        'infekcja układu moczowego': ['Interna', 'SOR'],
        'zapalenie opon mózgowych': ['Neurologia', 'SOR'],
        'zaostrzenie POChP': ['Interna', 'SOR'],
        'uraz wielonarządowy': ['Chirurgia', 'SOR']
    }
    
    for dept in DEPARTMENTS:
        df[f'compat_{dept}'] = 0
    
    for szablon, compatible_depts in szablon_to_depts.items():
        mask = df['szablon_przypadku'] == szablon
        for dept in compatible_depts:
            df.loc[mask, f'compat_{dept}'] = 1
    
    # ========================================================================
    # CECHY POCHODNE
    # ========================================================================
    
    logger.info("⚙️  Cechy pochodne...")
    
    df['is_high_priority'] = (df['kategoria_triażu'] <= 2).astype(int)
    df['avg_occupancy'] = df[[f'occ_{dept}' for dept in DEPARTMENTS]].mean(axis=1)
    df['max_occupancy_pct'] = df[[f'occ_pct_{dept}' for dept in DEPARTMENTS]].max(axis=1)
    
    # Future metrics
    df['avg_future_occupancy'] = df[[f'future_occ_{dept}' for dept in DEPARTMENTS]].mean(axis=1)
    df['max_future_occ_pct'] = df[[f'future_occ_pct_{dept}' for dept in DEPARTMENTS]].max(axis=1)
    
    # ========================================================================
    # POŁĄCZ WSZYSTKIE CECHY
    # ========================================================================
    
    logger.info("\n🔧 Łączenie wszystkich cech...")
    
    feature_columns = (
        ['wiek', 'płeć_encoded', 'kategoria_triażu'] +
        [f for f in patient_features if f in df.columns and f not in ['wiek', 'płeć', 'kategoria_triażu']] +
        list(szablon_dummies.columns) +
        occupancy_features +
        [f'compat_{dept}' for dept in DEPARTMENTS] +
        [f'future_occ_{dept}' for dept in DEPARTMENTS] +
        [f'future_occ_pct_{dept}' for dept in DEPARTMENTS] +
        [f'delta_occ_{dept}' for dept in DEPARTMENTS] +
        ['hour', 'day_of_week', 'is_weekend', 'is_night'] +
        ['is_high_priority', 'avg_occupancy', 'max_occupancy_pct',
         'avg_future_occupancy', 'max_future_occ_pct']
    )
    
    X = pd.concat([
        df[['wiek', 'płeć_encoded', 'kategoria_triażu']],
        df[[f for f in patient_features if f in df.columns and f not in ['wiek', 'płeć', 'kategoria_triażu']]],
        szablon_dummies,
        df[occupancy_features],
        df[[f'compat_{dept}' for dept in DEPARTMENTS]],
        df[[f'future_occ_{dept}' for dept in DEPARTMENTS]],
        df[[f'future_occ_pct_{dept}' for dept in DEPARTMENTS]],
        df[[f'delta_occ_{dept}' for dept in DEPARTMENTS]],
        df[['hour', 'day_of_week', 'is_weekend', 'is_night']],
        df[['is_high_priority', 'avg_occupancy', 'max_occupancy_pct',
            'avg_future_occupancy', 'max_future_occ_pct']]
    ], axis=1)
    
    # Target
    y = df['optymalne_przypisanie']
    
    # Filtruj - usuń Pediatria/Ginekologia (tylko 6 oddziałów w Model 3)
    valid_mask = y.isin(DEPARTMENTS)
    X_filtered = X[valid_mask].reset_index(drop=True)
    y_filtered = y[valid_mask].reset_index(drop=True)
    
    removed_count = len(X) - len(X_filtered)
    if removed_count > 0:
        logger.info(f"\n⚠️  Usunięto {removed_count} próbek z Pediatria/Ginekologia")
    
    logger.info(f"\n✓ Features gotowe: {X_filtered.shape}")
    logger.info(f"  Liczba cech: {X_filtered.shape[1]}")
    logger.info(f"  Liczba próbek: {len(X_filtered)}")
    logger.info(f"\n  Target distribution (po filtracji):")
    for dept in DEPARTMENTS:
        count = (y_filtered == dept).sum()
        pct = count / len(y_filtered) * 100
        logger.info(f"    {dept}: {count} ({pct:.1f}%)")
    
    return X_filtered, y_filtered, feature_columns


# ============================================================================
# 5. TRAIN/TEST SPLIT & NORMALIZATION
# ============================================================================

def prepare_train_test(X: pd.DataFrame, y: pd.Series):
    """Split i normalizacja danych"""
    print_header("Train/Test Split & Normalization")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split (stratified)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_encoded, test_size=0.3, random_state=RANDOM_STATE, stratify=y_encoded
    )
    
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=RANDOM_STATE, stratify=y_temp
    )
    
    logger.info(f"\n📊 Split:")
    logger.info(f"  Train: {len(X_train)} ({len(X_train)/len(X)*100:.0f}%)")
    logger.info(f"  Val:   {len(X_val)} ({len(X_val)/len(X)*100:.0f}%)")
    logger.info(f"  Test:  {len(X_test)} ({len(X_test)/len(X)*100:.0f}%)")
    
    # Normalizacja
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    logger.info(f"\n✓ Dane znormalizowane (RobustScaler)")
    
    return (X_train_scaled, X_val_scaled, X_test_scaled, 
            y_train, y_val, y_test, scaler, label_encoder)


# ============================================================================
# 6-9. TRAINING, EVALUATION, VISUALIZATION, SAVING
# (Pozostaje bez zmian - użyj z poprzedniego Model 3)
# ============================================================================

def train_models(train_data, val_data):
    """Trenuje różne modele klasyfikacji"""
    print_header("Trening modeli")
    
    X_train, y_train = train_data
    X_val, y_val = val_data
    
    models = {}
    
    # XGBoost
    logger.info("\n🔵 XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=7,
        learning_rate=0.1,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    models['XGBoost'] = xgb_model
    
    # Random Forest
    logger.info("🔵 Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    models['RandomForest'] = rf_model
    
    # MLP
    logger.info("🔵 MLP...")
    mlp_model = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        max_iter=300,
        random_state=RANDOM_STATE
    )
    mlp_model.fit(X_train, y_train)
    models['MLP'] = mlp_model
    
    logger.info(f"\n✓ Wytrenowano {len(models)} modeli")
    
    return models


def evaluate_models(models, test_data, label_encoder):
    """Ewaluuje modele"""
    print_header("Ewaluacja modeli")
    
    X_test, y_test = test_data
    
    results = {}
    
    for name, model in models.items():
        logger.info(f"\n🔍 {name}...")
        
        y_pred = model.predict(X_test)
        y_pred_labels = label_encoder.inverse_transform(y_pred)
        y_test_labels = label_encoder.inverse_transform(y_test)
        
        acc = accuracy_score(y_test, y_pred)
        bal_acc = balanced_accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        logger.info(f"  Accuracy:          {acc:.2%}")
        logger.info(f"  Balanced Accuracy: {bal_acc:.2%}")
        logger.info(f"  F1-Score:          {f1:.2%}")
        
        results[name] = {
            'accuracy': acc,
            'balanced_accuracy': bal_acc,
            'precision': prec,
            'recall': rec,
            'f1_score': f1,
            'y_pred': y_pred,
            'y_pred_labels': y_pred_labels
        }
    
    return results


def plot_confusion_matrices(results, test_data, label_encoder):
    """Wizualizuje confusion matrices"""
    X_test, y_test = test_data
    y_test_labels = label_encoder.inverse_transform(y_test)
    
    n_models = len(results)
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    axes = axes.flatten()
    
    for idx, (model_name, res) in enumerate(results.items()):
        ax = axes[idx]
        
        y_pred_labels = res['y_pred_labels']
        cm = confusion_matrix(y_test_labels, y_pred_labels, labels=DEPARTMENTS)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=DEPARTMENTS, yticklabels=DEPARTMENTS, ax=ax)
        
        ax.set_title(f'{model_name} - Accuracy: {res["accuracy"]:.2%}',
                     fontsize=12, fontweight='bold')
        ax.set_ylabel('True')
        ax.set_xlabel('Predicted')
    
    plt.tight_layout()
    
    filename = RESULTS_PATH / f'allocation_confusion_v{MODEL_VERSION}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    logger.info(f"✓ Saved: {filename}")
    plt.close()


def save_best_model(models, results, scaler, label_encoder, feature_columns):
    """Zapisuje najlepszy model"""
    print_header("Zapis najlepszego modelu")
    
    best_model_name = max(results, key=lambda x: results[x]['balanced_accuracy'])
    best_model = models[best_model_name]
    best_acc = results[best_model_name]['balanced_accuracy']
    
    logger.info(f"\n🏆 Najlepszy: {best_model_name}")
    logger.info(f"   Balanced Acc: {best_acc:.2%}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save model
    model_path = MODEL_PATH / f'allocation_{best_model_name.lower()}_v{MODEL_VERSION}_{timestamp}.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    logger.info(f"✓ Model: {model_path}")
    
    # Save artifacts
    artifacts_path = MODEL_PATH / f'allocation_artifacts_v{MODEL_VERSION}_{timestamp}.pkl'
    with open(artifacts_path, 'wb') as f:
        pickle.dump({
            'scaler': scaler,
            'label_encoder': label_encoder,
            'feature_columns': feature_columns,
            'departments': DEPARTMENTS,
            'model_version': MODEL_VERSION
        }, f)
    logger.info(f"✓ Artifacts: {artifacts_path}")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Główna funkcja pipeline"""
    
    print_header(f"MODEL 3 v{MODEL_VERSION} - REKOMENDACJA ALOKACJI")
    logger.info(f"🚀 Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Load data
    df_arr, df_triage = load_data()
    
    # 2. Load LSTM Model 2 (latest)
    lstm_model, lstm_scalers, lstm_metadata = load_latest_lstm_model()
    
    # 3. Prepare LSTM sequences
    X_seq, X_static, df_valid = prepare_lstm_sequences(df_arr, lstm_metadata)
    
    # 4. LSTM predictions (BATCH!)
    future_occupancy = predict_future_occupancy_batch(
        X_seq, X_static, lstm_model, lstm_scalers, batch_size=256
    )
    
    # 5. Feature engineering (z prawdziwymi LSTM predictions!)
    X, y, feature_columns = create_features(df_valid, df_triage, future_occupancy)
    
    # 6. Split & normalize
    train_test_data = prepare_train_test(X, y)
    X_train, X_val, X_test, y_train, y_val, y_test, scaler, label_encoder = train_test_data
    
    # 7. Train models
    models = train_models((X_train, y_train), (X_val, y_val))
    
    # 8. Evaluate
    results = evaluate_models(models, (X_test, y_test), label_encoder)
    
    # 9. Visualize
    plot_confusion_matrices(results, (X_test, y_test), label_encoder)
    
    # 10. Save
    save_best_model(models, results, scaler, label_encoder, feature_columns)
    
    # Summary
    print_header("PODSUMOWANIE")
    
    logger.info(f"\n✅ Model v{MODEL_VERSION} gotowy!")
    logger.info(f"\n📊 Wyniki:")
    for name, res in results.items():
        logger.info(f"  {name}: {res['balanced_accuracy']:.2%}")
    
    best = max(results, key=lambda x: results[x]['balanced_accuracy'])
    logger.info(f"\n🏆 Najlepszy: {best} ({results[best]['balanced_accuracy']:.2%})")
    
    print_header("ZAKOŃCZONO POMYŚLNIE ✅")


if __name__ == "__main__":
    main()
