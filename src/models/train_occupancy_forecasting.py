import pandas as pd
import numpy as np
import json
import pickle
import warnings
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# KONFIGURACJA
# ============================================================================

DATA_PATH = Path('data/raw/')
MODEL_PATH = Path('models/')
RESULTS_PATH = Path('results/')

MODEL_PATH.mkdir(parents=True, exist_ok=True)
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)

# Parametry modelu
LOOKBACK_HOURS = 48  # 2 dni historii dla LSTM
PREDICTION_HORIZON = 4  # Przewidujemy 4h do przodu
BATCH_SIZE = 64
EPOCHS = 100

DEPARTMENTS = ["SOR", "Interna", "Kardiologia", "Chirurgia", 
               "Ortopedia", "Neurologia", "Pediatria", "Ginekologia"]
N_DEPARTMENTS = len(DEPARTMENTS)

# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def print_header(text):
    """Wyświetla sformatowany nagłówek"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

# ============================================================================
# 1. WCZYTANIE I PREPROCESSING DANYCH
# ============================================================================

def load_and_preprocess_data():
    """Wczytuje i preprocessuje dane z CSV"""
    print_header("Wczytywanie danych")
    
    df = pd.read_csv(DATA_PATH / 'department_arrangement_data.csv')
    print(f"✓ Wczytano {len(df)} rekordów")
    
    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"  Zakres czasowy: {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"  Okres: {(df['timestamp'].max() - df['timestamp'].min()).days} dni")
    
    # Parse JSON obłożenia
    print("\n Parsowanie obłożenia oddziałów...")
    occupancy_data = []
    
    for idx, row in df.iterrows():
        occ_dict = json.loads(row['obłożenie_oddziałów'])
        occupancy_data.append([occ_dict[dept] for dept in DEPARTMENTS])
    
    occupancy_df = pd.DataFrame(occupancy_data, columns=DEPARTMENTS)
    
    # Dodaj cechy czasowe
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['day_of_month'] = df['timestamp'].dt.day
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    df['is_night'] = ((df['hour'] < 6) | (df['hour'] >= 22)).astype(int)
    
    # Połącz
    df_full = pd.concat([df[['timestamp', 'hour', 'day_of_week', 'month', 
                              'day_of_month', 'is_weekend', 'is_night']], 
                         occupancy_df], axis=1)
    
    print(f"✓ Dane przetworzone: {df_full.shape}")
    print(f"\n Pierwsze 3 rekordy:")
    print(df_full.head(3))
    
    return df_full

# ============================================================================
# 2. FEATURE ENGINEERING
# ============================================================================

def create_aggregate_features(df):
    """Tworzy cechy agregowane (7d, 30d średnie) dla sezonowości"""
    print_header("Feature Engineering - Agregaty długoterminowe")
    
    df_feat = df.copy()
    
    # Rolling averages dla każdego oddziału
    print("\n Obliczanie średnich kroczących...")
    
    for dept in DEPARTMENTS:
        # 7-dniowa średnia (168h)
        df_feat[f'{dept}_avg_7d'] = df[dept].rolling(window=168, min_periods=1).mean()
        
        # 30-dniowa średnia (720h)
        df_feat[f'{dept}_avg_30d'] = df[dept].rolling(window=720, min_periods=1).mean()
        
        # Odchylenie standardowe 7d (zmienność)
        df_feat[f'{dept}_std_7d'] = df[dept].rolling(window=168, min_periods=1).std().fillna(0)
    
    print(f"✓ Dodano cechy agregowane")
    print(f"  Rozmiar danych: {df_feat.shape}")
    
    return df_feat

def create_sequences(df, lookback=LOOKBACK_HOURS, horizon=PREDICTION_HORIZON):
    """
    Tworzy sekwencje dla LSTM.
    
    Returns:
        X_seq: (n_samples, lookback, n_departments) - sekwencje obłożenia
        X_static: (n_samples, n_static_features) - cechy czasowe i agregaty
        y: (n_samples, n_departments) - target obłożenie za 'horizon' godzin
    """
    print_header(f"Tworzenie sekwencji (lookback={lookback}h, horizon={horizon}h)")
    
    # Kolumny sekwencyjne (dla LSTM)
    seq_columns = DEPARTMENTS
    
    # Kolumny statyczne (dla Dense layer)
    static_columns = ['hour', 'day_of_week', 'month', 'day_of_month', 
                      'is_weekend', 'is_night']
    
    # Dodaj kolumny agregowane
    for dept in DEPARTMENTS:
        static_columns.extend([f'{dept}_avg_7d', f'{dept}_avg_30d', f'{dept}_std_7d'])
    
    X_seq_list = []
    X_static_list = []
    y_list = []
    
    # Sliding window
    for i in range(lookback, len(df) - horizon):
        # Sekwencja: ostatnie 'lookback' godzin
        seq = df[seq_columns].iloc[i-lookback:i].values
        X_seq_list.append(seq)
        
        # Static features: z ostatniego timestampu w oknie
        static = df[static_columns].iloc[i].values
        X_static_list.append(static)
        
        # Target: obłożenie za 'horizon' godzin
        target = df[seq_columns].iloc[i + horizon].values
        y_list.append(target)
        
        if (i - lookback) % 500 == 0:
            progress = (i - lookback) / (len(df) - horizon - lookback) * 100
            print(f"  Postęp: {progress:.1f}%", end='\r')
    
    X_seq = np.array(X_seq_list)
    X_static = np.array(X_static_list)
    y = np.array(y_list)
    
    print(f"\n✓ Utworzono {len(X_seq)} sekwencji")
    print(f"  X_seq shape:   {X_seq.shape}  (samples, timesteps, departments)")
    print(f"  X_static shape: {X_static.shape}  (samples, static_features)")
    print(f"  y shape:       {y.shape}  (samples, departments)")
    
    return X_seq, X_static, y

# ============================================================================
# 3. SPLIT DANYCH
# ============================================================================

def train_val_test_split(X_seq, X_static, y, train_ratio=0.7, val_ratio=0.15):
    """Dzieli dane chronologicznie (ważne dla time series!)"""
    print_header("Podział danych Train/Val/Test")
    
    n = len(X_seq)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    X_seq_train, X_static_train, y_train = X_seq[:train_end], X_static[:train_end], y[:train_end]
    X_seq_val, X_static_val, y_val = X_seq[train_end:val_end], X_static[train_end:val_end], y[train_end:val_end]
    X_seq_test, X_static_test, y_test = X_seq[val_end:], X_static[val_end:], y[val_end:]
    
    print(f"\n Podział chronologiczny:")
    print(f"  Train: {len(X_seq_train)} próbek ({train_ratio*100:.0f}%)")
    print(f"  Val:   {len(X_seq_val)} próbek ({val_ratio*100:.0f}%)")
    print(f"  Test:  {len(X_seq_test)} próbek ({(1-train_ratio-val_ratio)*100:.0f}%)")
    
    return (X_seq_train, X_static_train, y_train), \
           (X_seq_val, X_static_val, y_val), \
           (X_seq_test, X_static_test, y_test)

# ============================================================================
# 4. NORMALIZACJA
# ============================================================================

def normalize_data(train_data, val_data, test_data):
    """Normalizuje dane używając StandardScaler"""
    print_header("Normalizacja danych")
    
    X_seq_train, X_static_train, y_train = train_data
    X_seq_val, X_static_val, y_val = val_data
    X_seq_test, X_static_test, y_test = test_data
    
    # Scaler dla sekwencji (fit na train)
    seq_scaler = StandardScaler()
    X_seq_train_scaled = seq_scaler.fit_transform(
        X_seq_train.reshape(-1, N_DEPARTMENTS)
    ).reshape(X_seq_train.shape)
    
    X_seq_val_scaled = seq_scaler.transform(
        X_seq_val.reshape(-1, N_DEPARTMENTS)
    ).reshape(X_seq_val.shape)
    
    X_seq_test_scaled = seq_scaler.transform(
        X_seq_test.reshape(-1, N_DEPARTMENTS)
    ).reshape(X_seq_test.shape)
    
    # Scaler dla static features
    static_scaler = StandardScaler()
    X_static_train_scaled = static_scaler.fit_transform(X_static_train)
    X_static_val_scaled = static_scaler.transform(X_static_val)
    X_static_test_scaled = static_scaler.transform(X_static_test)
    
    # Target (y) też normalizujemy
    target_scaler = StandardScaler()
    y_train_scaled = target_scaler.fit_transform(y_train)
    y_val_scaled = target_scaler.transform(y_val)
    y_test_scaled = target_scaler.transform(y_test)
    
    print(f"✓ Dane znormalizowane")
    
    return (X_seq_train_scaled, X_static_train_scaled, y_train_scaled), \
           (X_seq_val_scaled, X_static_val_scaled, y_val_scaled), \
           (X_seq_test_scaled, X_static_test_scaled, y_test_scaled), \
           (seq_scaler, static_scaler, target_scaler)

# ============================================================================
# 5. BUDOWA MODELU LSTM
# ============================================================================

def build_lstm_model(seq_shape, static_shape, n_outputs=N_DEPARTMENTS):
    """
    Buduje multi-output LSTM z 2 inputami (Functional API).
    
    Args:
        seq_shape: (timesteps, features) dla LSTM
        static_shape: (n_static_features,) dla Dense
        n_outputs: liczba oddziałów do przewidzenia
    """
    print_header("Budowa modelu LSTM")
    
    # Input 1: Sekwencje czasowe (dla LSTM)
    input_seq = layers.Input(shape=seq_shape, name='sequence_input')
    
    # LSTM layers
    x = layers.LSTM(128, return_sequences=True, name='lstm_1')(input_seq)
    x = layers.Dropout(0.2)(x)
    x = layers.LSTM(64, name='lstm_2')(x)
    x = layers.Dropout(0.2)(x)
    
    # Input 2: Static features (cechy czasowe + agregaty)
    input_static = layers.Input(shape=(static_shape,), name='static_input')
    
    # Dense layers dla static
    s = layers.Dense(64, activation='relu', name='static_dense_1')(input_static)
    s = layers.Dropout(0.2)(s)
    s = layers.Dense(32, activation='relu', name='static_dense_2')(s)
    
    # Concatenate obu ścieżek
    combined = layers.Concatenate(name='concatenate')([x, s])
    
    # Final dense layers
    z = layers.Dense(128, activation='relu', name='dense_1')(combined)
    z = layers.Dropout(0.2)(z)
    z = layers.Dense(64, activation='relu', name='dense_2')(z)
    
    # Output: n_outputs neuronów (jeden per oddział)
    output = layers.Dense(n_outputs, activation='linear', name='output')(z)
    
    # Model
    model = Model(inputs=[input_seq, input_static], outputs=output, name='LSTM_MultiOutput')
    
    # Compile
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae']
    )
    
    print(f"\n✓ Model zbudowany")
    print(f"\n📐 Architektura:")
    model.summary()
    
    return model

# ============================================================================
# 6. TRENING MODELU
# ============================================================================

def train_model(model, train_data, val_data):
    """Trenuje model z callbackami"""
    print_header("Trening modelu")
    
    X_seq_train, X_static_train, y_train = train_data
    X_seq_val, X_static_val, y_val = val_data
    
    # Callbacks
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=15,
        restore_best_weights=True,
        verbose=1
    )
    
    checkpoint = ModelCheckpoint(
        MODEL_PATH / f'lstm_occupancy_best_{timestamp}.keras',
        monitor='val_loss',
        save_best_only=True,
        verbose=1
    )
    
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=7,
        min_lr=1e-6,
        verbose=1
    )
    
    print(f"\n Rozpoczynam trening (max {EPOCHS} epok)...")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Early stopping: patience=15")
    
    history = model.fit(
        [X_seq_train, X_static_train], y_train,
        validation_data=([X_seq_val, X_static_val], y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop, checkpoint, reduce_lr],
        verbose=1
    )
    
    print(f"\n✓ Trening zakończony")
    print(f"  Najlepsza val_loss: {min(history.history['val_loss']):.4f}")
    
    return history, timestamp

# ============================================================================
# 7. EWALUACJA
# ============================================================================

def evaluate_model(model, test_data, target_scaler):
    """Ewaluuje model na zbiorze testowym"""
    print_header("Ewaluacja modelu")
    
    X_seq_test, X_static_test, y_test_scaled = test_data
    
    # Predykcja
    print("\n Predykcja na zbiorze testowym...")
    y_pred_scaled = model.predict([X_seq_test, X_static_test], verbose=0)
    
    # Denormalizacja
    y_test = target_scaler.inverse_transform(y_test_scaled)
    y_pred = target_scaler.inverse_transform(y_pred_scaled)
    
    # Metryki globalne
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100
    
    print(f"\n Metryki globalne:")
    print(f"   MAE:  {mae:.2f} pacjentów")
    print(f"   RMSE: {rmse:.2f} pacjentów")
    print(f"   MAPE: {mape:.2f}%")
    
    # Metryki per oddział
    print(f"\n Metryki per oddział:")
    print(f"  {'Oddział':<15} {'MAE':<8} {'RMSE':<8} {'MAPE':<8}")
    print(f"  {'-'*45}")
    
    for i, dept in enumerate(DEPARTMENTS):
        dept_mae = mean_absolute_error(y_test[:, i], y_pred[:, i])
        dept_rmse = np.sqrt(mean_squared_error(y_test[:, i], y_pred[:, i]))
        dept_mape = np.mean(np.abs((y_test[:, i] - y_pred[:, i]) / (y_test[:, i] + 1e-8))) * 100
        
        print(f"  {dept:<15} {dept_mae:<8.2f} {dept_rmse:<8.2f} {dept_mape:<8.1f}%")
    
    # Directional accuracy
    direction_true = np.diff(y_test, axis=0) > 0
    direction_pred = np.diff(y_pred, axis=0) > 0
    directional_acc = np.mean(direction_true == direction_pred) * 100
    
    print(f"\n  Directional Accuracy: {directional_acc:.1f}%")
    
    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'directional_accuracy': directional_acc,
        'y_test': y_test,
        'y_pred': y_pred
    }

# ============================================================================
# 8. WIZUALIZACJE
# ============================================================================

def plot_predictions(results, n_samples=200):
    """Wizualizuje predykcje vs prawdziwe wartości"""
    print_header("Tworzenie wizualizacji")
    
    y_test = results['y_test'][-n_samples:]
    y_pred = results['y_pred'][-n_samples:]
    
    fig, axes = plt.subplots(4, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for i, dept in enumerate(DEPARTMENTS):
        ax = axes[i]
        ax.plot(y_test[:, i], label='Prawdziwe', linewidth=2, alpha=0.7)
        ax.plot(y_pred[:, i], label='Przewidywane', linewidth=2, alpha=0.7, linestyle='--')
        ax.set_title(f'{dept}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Timestep')
        ax.set_ylabel('Obłożenie')
        ax.legend()
        ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    filename = RESULTS_PATH / 'occupancy_predictions.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Zapisano: {filename}")
    
    plt.show()

def plot_training_history(history):
    """Wizualizuje historię treningu"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss
    ax1.plot(history.history['loss'], label='Train Loss')
    ax1.plot(history.history['val_loss'], label='Val Loss')
    ax1.set_title('Model Loss', fontweight='bold')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # MAE
    ax2.plot(history.history['mae'], label='Train MAE')
    ax2.plot(history.history['val_mae'], label='Val MAE')
    ax2.set_title('Model MAE', fontweight='bold')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('MAE')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    
    filename = RESULTS_PATH / 'training_history.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Zapisano: {filename}")
    
    plt.show()

# ============================================================================
# 9. ZAPIS MODELU
# ============================================================================

def save_artifacts(model, scalers, timestamp):
    """Zapisuje model i scalery"""
    print_header("Zapis modelu i artifacts")
    
    seq_scaler, static_scaler, target_scaler = scalers
    
    # Model
    model_path = MODEL_PATH / f'lstm_occupancy_final_{timestamp}.keras'
    model.save(model_path)
    print(f"✓ Model zapisany: {model_path}")
    
    # Scalery
    scalers_path = MODEL_PATH / f'lstm_scalers_{timestamp}.pkl'
    with open(scalers_path, 'wb') as f:
        pickle.dump({
            'seq_scaler': seq_scaler,
            'static_scaler': static_scaler,
            'target_scaler': target_scaler
        }, f)
    print(f"✓ Scalery zapisane: {scalers_path}")
    
    # Metadata
    metadata = {
        'lookback_hours': LOOKBACK_HOURS,
        'prediction_horizon': PREDICTION_HORIZON,
        'departments': DEPARTMENTS,
        'n_departments': N_DEPARTMENTS,
        'timestamp': timestamp
    }
    
    metadata_path = MODEL_PATH / f'lstm_metadata_{timestamp}.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata zapisana: {metadata_path}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Główna funkcja pipeline"""
    
    print_header("MULTI-OUTPUT LSTM - PROGNOZOWANIE OBCIĄŻENIA ODDZIAŁÓW")
    print(f"Data rozpoczęcia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Load data
    df = load_and_preprocess_data()
    
    # 2. Feature engineering
    df_feat = create_aggregate_features(df)
    
    # 3. Create sequences
    X_seq, X_static, y = create_sequences(df_feat)
    
    # 4. Split
    train_data, val_data, test_data = train_val_test_split(X_seq, X_static, y)
    
    # 5. Normalize
    train_norm, val_norm, test_norm, scalers = normalize_data(train_data, val_data, test_data)
    
    # 6. Build model
    seq_shape = (LOOKBACK_HOURS, N_DEPARTMENTS)
    static_shape = train_norm[1].shape[1]
    model = build_lstm_model(seq_shape, static_shape)
    
    # 7. Train
    history, timestamp = train_model(model, train_norm, val_norm)
    
    # 8. Evaluate
    results = evaluate_model(model, test_norm, scalers[2])
    
    # 9. Visualize
    plot_training_history(history)
    plot_predictions(results)
    
    # 10. Save
    save_artifacts(model, scalers, timestamp)
    
    print_header("ZAKOŃCZONO POMYŚLNIE")
    print(f"\n Podsumowanie:")
    print(f"   MAE:  {results['mae']:.2f} pacjentów")
    print(f"   RMSE: {results['rmse']:.2f} pacjentów")
    print(f"   MAPE: {results['mape']:.2f}%")
    print(f"   Directional Accuracy: {results['directional_accuracy']:.1f}%")
    print(f"\n Model gotowy do użycia!")

if __name__ == "__main__":
    main()
