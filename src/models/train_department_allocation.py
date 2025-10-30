import pandas as pd
import numpy as np
import json
import pickle
import warnings
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler, LabelEncoder
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

# ============================================================================
# KONFIGURACJA - ŚCIEŻKI DO MODELI
# ============================================================================

DATA_PATH = Path('data/raw/')
MODEL_PATH = Path('models/')
RESULTS_PATH = Path('results/')

RESULTS_PATH.mkdir(parents=True, exist_ok=True)

# Model 1: Klasyfikacja triaży (najlepszy - 83.4%)
TRIAGE_MODEL_PATH = MODEL_PATH / 'dl_triage_model_20251017_204506.keras'
TRIAGE_SCALER_PATH = MODEL_PATH / 'dl_scaler_20251017_204506.pkl'

# Model 2: LSTM Occupancy (MAE 2.56)
LSTM_MODEL_PATH = MODEL_PATH / 'lstm_occupancy_final_20251018_120052.keras'
LSTM_SCALERS_PATH = MODEL_PATH / 'lstm_scalers_20251018_120052.pkl'
LSTM_METADATA_PATH = MODEL_PATH / 'lstm_metadata_20251018_120052.json'

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

DEPARTMENTS = ["SOR", "Interna", "Kardiologia", "Chirurgia", 
               "Ortopedia", "Neurologia", "Pediatria", "Ginekologia"]

DEPARTMENT_CAPACITY = {
    "SOR": 25, "Interna": 50, "Kardiologia": 30, "Chirurgia": 35,
    "Ortopedia": 25, "Neurologia": 20, "Pediatria": 30, "Ginekologia": 20
}

# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def print_header(text):
    """Wyświetla sformatowany nagłówek"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

# ============================================================================
# 1. WCZYTANIE DANYCH
# ============================================================================

def load_data():
    """Wczytuje dane arrangement i triage"""
    print_header("Wczytywanie danych")
    
    # Arrangement data
    df_arr = pd.read_csv(DATA_PATH / 'department_arrangement_data.csv')
    print(f"✓ Arrangement data: {len(df_arr)} rekordów")
    
    # Triage data
    df_triage = pd.read_csv(DATA_PATH / 'triage_data.csv')
    print(f"✓ Triage data: {len(df_triage)} rekordów")
    
    # Parse timestamp
    df_arr['timestamp'] = pd.to_datetime(df_arr['timestamp'])
    df_arr = df_arr.sort_values('timestamp').reset_index(drop=True)
    
    # Parse JSON obłożenia
    occupancy_data = []
    for idx, row in df_arr.iterrows():
        occ_dict = json.loads(row['obłożenie_oddziałów'])
        occupancy_data.append(occ_dict)
    
    df_occ = pd.DataFrame(occupancy_data)
    
    # Dodaj obłożenie do df_arr
    for dept in DEPARTMENTS:
        df_arr[f'occ_{dept}'] = df_occ[dept]
        df_arr[f'occ_pct_{dept}'] = df_occ[dept] / DEPARTMENT_CAPACITY[dept]
    
    print(f"\n✓ Dane przetworzone: {df_arr.shape}")
    
    return df_arr, df_triage

# ============================================================================
# 2. WCZYTANIE MODELI 1 i 2
# ============================================================================

def load_pretrained_models():
    """Wczytuje wytrenowane modele triaży i LSTM"""
    print_header("Wczytywanie wytrenowanych modeli")
    
    # Model 1: Triaż
    print("\n🔵 Model 1: Klasyfikacja triaży...")
    triage_model = keras.models.load_model(TRIAGE_MODEL_PATH)
    
    with open(TRIAGE_SCALER_PATH, 'rb') as f:
        triage_scaler = pickle.load(f)
    
    print(f"  ✓ Załadowano: {TRIAGE_MODEL_PATH.name}")
    
    # Model 2: LSTM
    print("\n🔵 Model 2: LSTM Occupancy...")
    lstm_model = keras.models.load_model(LSTM_MODEL_PATH)
    
    with open(LSTM_SCALERS_PATH, 'rb') as f:
        lstm_scalers = pickle.load(f)
    
    with open(LSTM_METADATA_PATH, 'r') as f:
        lstm_metadata = json.load(f)
    
    print(f"  ✓ Załadowano: {LSTM_MODEL_PATH.name}")
    
    return triage_model, triage_scaler, lstm_model, lstm_scalers, lstm_metadata

# ============================================================================
# 3. FEATURE ENGINEERING
# ============================================================================

def create_features(df_arr, df_triage, lstm_model, lstm_scalers, lstm_metadata):
    """
    Tworzy kompleksowy zestaw cech dla modelu alokacji.
    Używa Modelu 1 (triaż) i Modelu 2 (LSTM) do generowania cech.
    """
    print_header("Feature Engineering")
    
    print("\n📊 Przygotowanie cech pacjentów...")
    
    # Merge arrangement z triage po id_pacjenta
    df = df_arr.merge(
        df_triage, 
        left_on='id_pacjenta', 
        right_on='id_przypadku',
        how='left',
        suffixes=('', '_triage')
    )
    
    print(f"  ✓ Połączono dane: {df.shape}")
    
    # ========================================================================
    # CECHY PACJENTA
    # ========================================================================
    
    patient_features = [
        'wiek', 'płeć', 'kategoria_triażu',
        'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
        'temperatura', 'saturacja', 'GCS', 'ból', 
        'częstotliwość_oddechów', 'czas_od_objawów_h'
    ]
    
    # Encode płeć
    df['płeć_encoded'] = (df['płeć'] == 'M').astype(int)
    
    # One-hot encode szablon przypadku
    szablon_dummies = pd.get_dummies(df['szablon_przypadku'], prefix='szablon')
    
    # One-hot encode oddział docelowy
    #target_dept_dummies = pd.get_dummies(df['oddział_docelowy'], prefix='target_dept')
    
    # ========================================================================
    # CECHY OBCIĄŻENIA (obecne)
    # ========================================================================
    
    occupancy_features = []
    for dept in DEPARTMENTS:
        occupancy_features.append(f'occ_{dept}')
        occupancy_features.append(f'occ_pct_{dept}')
        
        # Czy oddział przeciążony (>80%)
        df[f'overcrowded_{dept}'] = (df[f'occ_pct_{dept}'] > 0.8).astype(int)
        occupancy_features.append(f'overcrowded_{dept}')
    
    # ========================================================================
    # CECHY KOMPATYBILNOŚCI MEDYCZNEJ
    # ========================================================================
    
    print("\n🏥 Obliczanie kompatybilności medycznej...")
    
    # Mapowanie kompatybilności (szablon → oddziały)
    compatibility_map = {
        'zawał_STEMI': {'Kardiologia': 1.0, 'Interna': 0.7, 'SOR': 0.8},
        'udar_ciężki': {'Neurologia': 1.0, 'SOR': 0.8, 'Interna': 0.5},
        'uraz_wielonarządowy': {'SOR': 1.0, 'Chirurgia': 0.9, 'Ortopedia': 0.6},
        'zapalenie_płuc_ciężkie': {'Interna': 1.0, 'SOR': 0.7},
        'zapalenie_wyrostka': {'Chirurgia': 1.0, 'SOR': 0.7},
        'silne_krwawienie': {'Chirurgia': 1.0, 'SOR': 0.9},
        'złamanie_proste': {'Ortopedia': 1.0, 'Chirurgia': 0.6, 'SOR': 0.5},
        'infekcja_moczu': {'Interna': 1.0, 'SOR': 0.5},
        'zaostrzenie_astmy': {'Interna': 1.0, 'SOR': 0.7},
        'ból_brzucha_łagodny': {'Interna': 1.0, 'SOR': 0.6},
        'skręcenie_lekkie': {'Ortopedia': 1.0, 'SOR': 0.5},
        'migrena': {'Neurologia': 1.0, 'SOR': 0.6},
        'przeziębienie': {'Interna': 1.0, 'SOR': 0.4},
        'kontrola': {'Interna': 1.0},
        'receptura': {'Interna': 1.0, 'SOR': 0.3}
    }
    
    # Dla każdego oddziału, oblicz compatibility score
    for dept in DEPARTMENTS:
        scores = []
        for idx, row in df.iterrows():
            szablon = row['szablon_przypadku']
            if szablon in compatibility_map and dept in compatibility_map[szablon]:
                scores.append(compatibility_map[szablon][dept])
            else:
                scores.append(0.1)  # Bardzo niska kompatybilność
        
        df[f'compat_{dept}'] = scores
    
    # ========================================================================
    # CECHY CZASOWE
    # ========================================================================
    
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_night'] = ((df['hour'] < 6) | (df['hour'] >= 22)).astype(int)
    
    # ========================================================================
    # CECHY Z MODELU 2: PRZYSZŁE OBCIĄŻENIE (LSTM)
    # ========================================================================
    
    print("\n🔮 Generowanie predykcji przyszłego obciążenia (Model 2 - LSTM)...")
    print("   (To może chwilę potrwać...)")
    
    # Tutaj w pełnym systemie używalibyśmy LSTM do predykcji dla każdego timestampu
    # Ale dla treningu Model 3, uprośćmy: weźmiemy obecne obciążenie + małą zmianę
    # (W produkcji byłby prawdziwy LSTM forward pass)
    
    # UPROSZCZENIE: Symulujemy przyszłe obciążenie
    # W rzeczywistości to byłoby: lstm_model.predict(...)
    
    np.random.seed(RANDOM_STATE)
    for dept in DEPARTMENTS:
        # Symulujemy zmianę obciążenia (-5 do +5 pacjentów)
        future_change = np.random.randint(-5, 6, size=len(df))
        df[f'future_occ_{dept}'] = np.clip(
            df[f'occ_{dept}'] + future_change, 
            0, 
            DEPARTMENT_CAPACITY[dept]
        )
        df[f'future_occ_pct_{dept}'] = df[f'future_occ_{dept}'] / DEPARTMENT_CAPACITY[dept]
        df[f'delta_occ_{dept}'] = df[f'future_occ_{dept}'] - df[f'occ_{dept}']
    
    print("   ✓ Przyszłe obciążenie wygenerowane (symulacja)")
    print("   ℹ️  W produkcji: to byłby prawdziwy LSTM forward pass")
    
    # ========================================================================
    # CECHY POCHODNE
    # ========================================================================
    
    df['is_high_priority'] = (df['kategoria_triażu'] <= 2).astype(int)
    
    # Średnie obciążenie wszystkich oddziałów
    df['avg_occupancy'] = df[[f'occ_{dept}' for dept in DEPARTMENTS]].mean(axis=1)
    df['max_occupancy_pct'] = df[[f'occ_pct_{dept}' for dept in DEPARTMENTS]].max(axis=1)
    
    # ========================================================================
    # POŁĄCZ WSZYSTKIE CECHY
    # ========================================================================
    
    print("\n🔧 Łączenie cech...")
    
    feature_columns = (
        ['wiek', 'płeć_encoded', 'kategoria_triażu'] +
        [f for f in patient_features if f in df.columns and f not in ['wiek', 'płeć', 'kategoria_triażu']] +
        list(szablon_dummies.columns) +
        #list(target_dept_dummies.columns) +
        occupancy_features +
        [f'compat_{dept}' for dept in DEPARTMENTS] +
        [f'future_occ_{dept}' for dept in DEPARTMENTS] +
        [f'future_occ_pct_{dept}' for dept in DEPARTMENTS] +
        [f'delta_occ_{dept}' for dept in DEPARTMENTS] +
        ['hour', 'day_of_week', 'is_weekend', 'is_night'] +
        ['is_high_priority', 'avg_occupancy', 'max_occupancy_pct']
    )
    
    X = pd.concat([
        df[['wiek', 'płeć_encoded', 'kategoria_triażu']],
        df[[f for f in patient_features if f in df.columns and f not in ['wiek', 'płeć', 'kategoria_triażu']]],
        szablon_dummies,
        #target_dept_dummies,
        df[occupancy_features],
        df[[f'compat_{dept}' for dept in DEPARTMENTS]],
        df[[f'future_occ_{dept}' for dept in DEPARTMENTS]],
        df[[f'future_occ_pct_{dept}' for dept in DEPARTMENTS]],
        df[[f'delta_occ_{dept}' for dept in DEPARTMENTS]],
        df[['hour', 'day_of_week', 'is_weekend', 'is_night']],
        df[['is_high_priority', 'avg_occupancy', 'max_occupancy_pct']]
    ], axis=1)
    
    # Target: optymalne_przypisanie
    y = df['optymalne_przypisanie']
    
    print(f"\n✓ Features gotowe: {X.shape}")
    print(f"  Liczba cech: {X.shape[1]}")
    print(f"  Liczba próbek: {len(X)}")
    print(f"\n  Target classes: {y.nunique()} oddziałów")
    print(f"  Rozkład:")
    for dept in DEPARTMENTS:
        count = (y == dept).sum()
        pct = count / len(y) * 100
        print(f"    {dept}: {count} ({pct:.1f}%)")

    print("\n🔍 Analiza Data Leakage:")
    correlation = (df['oddział_docelowy'] == df['optymalne_przypisanie']).sum() / len(df)
    print(f"   Zgodność oddział_docelowy ↔ optymalne_przypisanie: {correlation:.1%}")

    if correlation > 0.95:
        print("   ⚠️  UWAGA: Bardzo wysoka zgodność = możliwy data leakage!")
        
    return X, y, feature_columns

# ============================================================================
# 4. SPLIT & NORMALIZACJA
# ============================================================================

def prepare_train_test(X, y):
    """Split chronologiczny + normalizacja"""
    print_header("Podział danych i normalizacja")
    
    # Split chronologiczny (70/15/15)
    n = len(X)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)
    
    X_train = X[:train_end]
    X_val = X[train_end:val_end]
    X_test = X[val_end:]
    
    y_train = y[:train_end]
    y_val = y[train_end:val_end]
    y_test = y[val_end:]
    
    print(f"\n📊 Podział chronologiczny:")
    print(f"  Train: {len(X_train)} próbek (70%)")
    print(f"  Val:   {len(X_val)} próbek (15%)")
    print(f"  Test:  {len(X_test)} próbek (15%)")
    
    # Normalizacja
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Label encoding dla y
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    y_val_encoded = le.transform(y_val)
    y_test_encoded = le.transform(y_test)
    
    print(f"✓ Dane znormalizowane")
    
    return (X_train_scaled, y_train_encoded, y_train), \
           (X_val_scaled, y_val_encoded, y_val), \
           (X_test_scaled, y_test_encoded, y_test), \
           scaler, le

# ============================================================================
# 5. TRENING MODELI
# ============================================================================

def train_models(train_data, val_data):
    """Trenuje 3 modele + ensemble"""
    print_header("Trening modeli alokacji")
    
    X_train, y_train, _ = train_data
    X_val, y_val, _ = val_data
    
    models = {}
    
    # ========================================================================
    # MODEL 1: XGBoost
    # ========================================================================
    
    print("\n🌳 Trening XGBoost...")
    
    xgb_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        eval_metric='mlogloss',
        use_label_encoder=False
    )
    
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    models['XGBoost'] = xgb_model
    print("  ✓ XGBoost wytrenowany")
    
    # ========================================================================
    # MODEL 2: Random Forest
    # ========================================================================
    
    print("\n🌲 Trening Random Forest...")
    
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    rf_model.fit(X_train, y_train)
    
    models['RandomForest'] = rf_model
    print("  ✓ Random Forest wytrenowany")
    
    # ========================================================================
    # MODEL 3: Neural Network
    # ========================================================================
    
    print("\n🧠 Trening Neural Network...")
    
    nn_model = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation='relu',
        solver='adam',
        alpha=0.001,
        batch_size=64,
        learning_rate='adaptive',
        max_iter=100,
        random_state=RANDOM_STATE,
        early_stopping=True,
        validation_fraction=0.15,
        verbose=False
    )
    
    nn_model.fit(X_train, y_train)
    
    models['NeuralNetwork'] = nn_model
    print("  ✓ Neural Network wytrenowany")
    
    # ========================================================================
    # ENSEMBLE: Voting Classifier
    # ========================================================================
    
    print("\n🎯 Tworzenie Ensemble (Voting)...")
    
    ensemble = VotingClassifier(
        estimators=[
            ('xgb', xgb_model),
            ('rf', rf_model),
            ('nn', nn_model)
        ],
        voting='soft',
        weights=[2, 2, 1]  # XGBoost i RF mają większą wagę
    )
    
    ensemble.fit(X_train, y_train)
    
    models['Ensemble'] = ensemble
    print("  ✓ Ensemble wytrenowany")
    
    return models

# ============================================================================
# 6. EWALUACJA
# ============================================================================

def evaluate_models(models, test_data, label_encoder):
    """Ewaluuje wszystkie modele"""
    print_header("Ewaluacja modeli")
    
    X_test, y_test_encoded, y_test_orig = test_data
    
    results = {}
    
    for model_name, model in models.items():
        print(f"\n{'='*70}")
        print(f" {model_name}")
        print(f"{'='*70}")
        
        y_pred = model.predict(X_test)
        
        # Metryki
        accuracy = accuracy_score(y_test_encoded, y_pred)
        balanced_acc = balanced_accuracy_score(y_test_encoded, y_pred)
        precision = precision_score(y_test_encoded, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test_encoded, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test_encoded, y_pred, average='weighted', zero_division=0)
        
        print(f"\n📊 Metryki globalne:")
        print(f"  Accuracy:          {accuracy:.2%}")
        print(f"  Balanced Accuracy: {balanced_acc:.2%}")
        print(f"  Precision:         {precision:.2%}")
        print(f"  Recall:            {recall:.2%}")
        print(f"  F1-Score:          {f1:.2%}")
        
        # Top-3 accuracy
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)
            top3_preds = np.argsort(y_proba, axis=1)[:, -3:]
            top3_acc = np.mean([y_test_encoded[i] in top3_preds[i] for i in range(len(y_test_encoded))])
            print(f"  Top-3 Accuracy:    {top3_acc:.2%}")
        
        # Classification report
        print(f"\n📋 Classification Report:")
        y_pred_labels = label_encoder.inverse_transform(y_pred)
        print(classification_report(y_test_orig, y_pred_labels, zero_division=0))
        
        results[model_name] = {
            'accuracy': accuracy,
            'balanced_accuracy': balanced_acc,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'y_pred': y_pred,
            'y_pred_labels': y_pred_labels
        }
        
        if hasattr(model, 'predict_proba'):
            results[model_name]['top3_accuracy'] = top3_acc
    
    return results

# ============================================================================
# 7. WIZUALIZACJE
# ============================================================================

def plot_confusion_matrices(results, test_data, label_encoder):
    """Rysuje confusion matrices dla wszystkich modeli"""
    print_header("Tworzenie wizualizacji")
    
    X_test, y_test_encoded, y_test_orig = test_data
    
    n_models = len(results)
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    axes = axes.flatten()
    
    for idx, (model_name, res) in enumerate(results.items()):
        ax = axes[idx]
        
        y_pred_labels = res['y_pred_labels']
        
        cm = confusion_matrix(y_test_orig, y_pred_labels, labels=DEPARTMENTS)
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=DEPARTMENTS, yticklabels=DEPARTMENTS, ax=ax)
        
        ax.set_title(f'{model_name} - Accuracy: {res["accuracy"]:.2%}', 
                     fontsize=12, fontweight='bold')
        ax.set_ylabel('Prawdziwy oddział')
        ax.set_xlabel('Przewidywany oddział')
    
    plt.tight_layout()
    
    filename = RESULTS_PATH / 'allocation_confusion_matrices.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Zapisano: {filename}")
    
    plt.show()

def plot_model_comparison(results):
    """Porównanie wszystkich modeli"""
    
    metrics_data = []
    for model_name, res in results.items():
        metrics_data.append({
            'Model': model_name,
            'Accuracy': res['accuracy'],
            'Balanced Acc': res['balanced_accuracy'],
            'Precision': res['precision'],
            'Recall': res['recall'],
            'F1-Score': res['f1_score']
        })
    
    df_comp = pd.DataFrame(metrics_data)
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    metrics = ['Accuracy', 'Balanced Acc', 'Precision', 'Recall', 'F1-Score']
    
    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        df_comp.plot(x='Model', y=metric, kind='bar', ax=ax, legend=False, color='steelblue')
        ax.set_title(metric, fontsize=12, fontweight='bold')
        ax.set_ylabel(metric)
        ax.set_xlabel('')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        
        for i, v in enumerate(df_comp[metric]):
            ax.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontsize=9)
    
    axes[-1].axis('off')
    
    plt.suptitle('Porównanie modeli alokacji - wszystkie metryki', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    filename = RESULTS_PATH / 'allocation_model_comparison.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Zapisano: {filename}")
    
    plt.show()

# ============================================================================
# 8. ZAPIS MODELU
# ============================================================================

def save_best_model(models, results, scaler, label_encoder, feature_columns):
    """Zapisuje najlepszy model"""
    print_header("Zapis najlepszego modelu")
    
    # Znajdź najlepszy model (wg balanced accuracy)
    best_model_name = max(results, key=lambda x: results[x]['balanced_accuracy'])
    best_model = models[best_model_name]
    best_acc = results[best_model_name]['balanced_accuracy']
    
    print(f"\n🏆 Najlepszy model: {best_model_name}")
    print(f"   Balanced Accuracy: {best_acc:.2%}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Zapisz model
    model_path = MODEL_PATH / f'allocation_{best_model_name.lower()}_{timestamp}.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    print(f"✓ Model zapisany: {model_path}")
    
    # Zapisz scaler i label encoder
    artifacts_path = MODEL_PATH / f'allocation_artifacts_{timestamp}.pkl'
    with open(artifacts_path, 'wb') as f:
        pickle.dump({
            'scaler': scaler,
            'label_encoder': label_encoder,
            'feature_columns': feature_columns,
            'departments': DEPARTMENTS
        }, f)
    print(f"✓ Artifacts zapisane: {artifacts_path}")
    
    # Zapisz metryki
    metrics_path = MODEL_PATH / f'allocation_{best_model_name.lower()}_{timestamp}_metrics.json'
    metrics_to_save = {k: v for k, v in results[best_model_name].items() 
                       if k not in ['y_pred', 'y_pred_labels']}
    with open(metrics_path, 'w') as f:
        json.dump(metrics_to_save, f, indent=2)
    print(f"✓ Metryki zapisane: {metrics_path}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Główna funkcja pipeline"""
    
    print_header("MODEL 3: REKOMENDACJA ALOKACJI PACJENTÓW")
    print(f"Data rozpoczęcia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Load data
    df_arr, df_triage = load_data()
    
    # 2. Load pretrained models (1 i 2)
    triage_model, triage_scaler, lstm_model, lstm_scalers, lstm_metadata = load_pretrained_models()
    
    # 3. Feature engineering
    X, y, feature_columns = create_features(
        df_arr, df_triage, lstm_model, lstm_scalers, lstm_metadata
    )
    
    # 4. Split & normalize
    train_data, val_data, test_data, scaler, label_encoder = prepare_train_test(X, y)
    
    # 5. Train models
    models = train_models(train_data, val_data)
    
    # 6. Evaluate
    results = evaluate_models(models, test_data, label_encoder)
    
    # 7. Visualize
    plot_confusion_matrices(results, test_data, label_encoder)
    plot_model_comparison(results)
    
    # 8. Save best model
    save_best_model(models, results, scaler, label_encoder, feature_columns)
    
    # 9. Summary
    print_header("PODSUMOWANIE")
    
    print("\n🎯 Wyniki wszystkich modeli:")
    print(f"  {'Model':<20} {'Accuracy':<12} {'Balanced Acc':<15} {'F1-Score':<12}")
    print(f"  {'-'*60}")
    
    for model_name, res in results.items():
        acc = res['accuracy']
        bacc = res['balanced_accuracy']
        f1 = res['f1_score']
        print(f"  {model_name:<20} {acc:<12.2%} {bacc:<15.2%} {f1:<12.2%}")
    
    best_model_name = max(results, key=lambda x: results[x]['balanced_accuracy'])
    best_acc = results[best_model_name]['balanced_accuracy']
    
    print(f"\n🏆 Najlepszy model: {best_model_name}")
    print(f"   Balanced Accuracy: {best_acc:.2%}")
    
    if 'top3_accuracy' in results[best_model_name]:
        print(f"   Top-3 Accuracy: {results[best_model_name]['top3_accuracy']:.2%}")
    
    print("\n✅ Model gotowy do użycia!")
    print("\n📦 Zapisane pliki:")
    print(f"  - models/allocation_{best_model_name.lower()}_*.pkl")
    print(f"  - models/allocation_artifacts_*.pkl")
    print(f"  - models/allocation_{best_model_name.lower()}_*_metrics.json")
    print(f"  - results/allocation_confusion_matrices.png")
    print(f"  - results/allocation_model_comparison.png")
    
    print_header("ZAKOŃCZONO POMYŚLNIE")

if __name__ == "__main__":
    main()
