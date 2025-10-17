"""
SKRYPT TESTOWY DLA DEEP LEARNING MODELU
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import tensorflow as tf
from tensorflow import keras

print("="*70)
print("TESTOWANIE DEEP LEARNING MODELU TRIAŻY")
print("="*70)

# ============================================================================
# KONFIGURACJA
# ============================================================================
DATA_PATH = Path('/home/dolfik/Projects/Clinic-data/data/processed/')
MODEL_PATH = Path('/home/dolfik/Projects/Clinic-data/models/')

# ============================================================================
# 1. ZNAJDŹ NAJNOWSZY MODEL
# ============================================================================
print("\nSzukanie najnowszego modelu...")

keras_models = list(MODEL_PATH.glob('dl_triage_model_*.keras'))
if not keras_models:
    print("❌ Nie znaleziono modeli DL!")
    print("   Najpierw uruchom: python train_deep_learning_triage.py")
    exit(1)

latest_model = max(keras_models, key=lambda p: p.stat().st_mtime)
timestamp = latest_model.stem.split('_')[-1]

print(f"✓ Znaleziono model: {latest_model.name}")

# Znajdź odpowiadający scaler
scaler_path = MODEL_PATH / f'dl_scaler_{timestamp}.pkl'
if not scaler_path.exists():
    print(f"❌ Nie znaleziono scalera: {scaler_path}")
    exit(1)

print(f"✓ Znaleziono scaler: {scaler_path.name}")

# ============================================================================
# 2. WCZYTAJ MODEL I SCALER
# ============================================================================
print("\nŁadowanie modelu...")

model = keras.models.load_model(latest_model)
print(f"✓ Model załadowany")

with open(scaler_path, 'rb') as f:
    scaler = pickle.load(f)
print(f"✓ Scaler załadowany")

# ============================================================================
# 3. WCZYTAJ DANE TESTOWE
# ============================================================================
print("\nŁadowanie danych testowych...")

X_test = pd.read_csv(DATA_PATH / 'X_test.csv')
y_test = pd.read_csv(DATA_PATH / 'y_test.csv').values.ravel()

# Usuń kolumny tekstowe
text_cols = X_test.select_dtypes(include=['object']).columns
if len(text_cols) > 0:
    X_test = X_test.drop(columns=text_cols)

X_test = X_test.astype(float)

print(f"✓ Dane testowe: {X_test.shape[0]} przypadków, {X_test.shape[1]} cech")

# ============================================================================
# 4. FEATURE ENGINEERING (MUSI BYĆ IDENTYCZNY JAK PODCZAS TRENINGU)
# ============================================================================
print("\nFeature engineering...")

def create_dl_features(X):
    """Identyczny jak w train_deep_learning_triage.py"""
    X_eng = X.copy()
    
    if 'wiek' in X.columns and 'tętno' in X.columns:
        X_eng['wiek_x_tetno'] = X['wiek'] * X['tętno']
    
    if 'ciśnienie_skurczowe' in X.columns and 'ciśnienie_rozkurczowe' in X.columns:
        X_eng['cisnienie_pulsowe'] = X['ciśnienie_skurczowe'] - X['ciśnienie_rozkurczowe']
        X_eng['srednie_cisnienie'] = (X['ciśnienie_skurczowe'] + 2*X['ciśnienie_rozkurczowe']) / 3
    
    if 'tętno' in X.columns and 'ciśnienie_skurczowe' in X.columns:
        with np.errstate(divide='ignore', invalid='ignore'):
            shock_idx = X['tętno'] / X['ciśnienie_skurczowe']
            X_eng['shock_index'] = np.where(np.isfinite(shock_idx), shock_idx, 0)
    
    if 'wiek' in X.columns:
        X_eng['wiek_dziecko'] = (X['wiek'] < 18).astype(float)
        X_eng['wiek_senior'] = (X['wiek'] > 65).astype(float)
    
    if 'temperatura' in X.columns:
        X_eng['goraczka'] = (X['temperatura'] > 38.0).astype(float)
        X_eng['goraczka_wysoka'] = (X['temperatura'] > 39.0).astype(float)
    
    if 'saturacja' in X.columns:
        X_eng['hipoksja'] = (X['saturacja'] < 90).astype(float)
        X_eng['hipoksja_ciezka'] = (X['saturacja'] < 85).astype(float)
    
    return X_eng

X_test_eng = create_dl_features(X_test)
print(f"✓ Cechy rozszerzone: {X_test.shape[1]} → {X_test_eng.shape[1]}")

# ============================================================================
# 5. NORMALIZACJA
# ============================================================================
print("\nNormalizacja...")

X_test_scaled = scaler.transform(X_test_eng)
print(f"✓ Dane znormalizowane")

# ============================================================================
# 6. PREDYKCJA
# ============================================================================
print("\nPredykcja...")

y_pred_proba = model.predict(X_test_scaled, verbose=0)
y_pred = np.argmax(y_pred_proba, axis=1) + 1  # +1 bo kategorie to 1-5

print(f"✓ Predykcja zakończona")

# ============================================================================
# 7. EWALUACJA
# ============================================================================
print("\n" + "="*70)
print("WYNIKI NA ZBIORZE TESTOWYM")
print("="*70)

from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score, 
    classification_report
)

accuracy = accuracy_score(y_test, y_pred)
balanced_acc = balanced_accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\n🎯 Główne metryki:")
print(f"   Accuracy:          {accuracy:.2%}")
print(f"   Balanced Accuracy: {balanced_acc:.2%}")
print(f"   F1-Score:          {f1:.2%}")

print(f"\n📊 Dokładność per kategoria:")
for cat in range(1, 6):
    mask = y_test == cat
    if mask.sum() > 0:
        cat_acc = (y_pred[mask] == cat).sum() / mask.sum()
        total = mask.sum()
        correct = (y_pred[mask] == cat).sum()
        print(f"   Kategoria {cat}: {cat_acc:.1%} ({correct}/{total})")

# ============================================================================
# 8. PRZYKŁADOWE PREDYKCJE
# ============================================================================
print("\n" + "="*70)
print("PRZYKŁADOWE PREDYKCJE")
print("="*70)

np.random.seed(42)
sample_indices = np.random.choice(len(X_test), size=5, replace=False)

for idx in sample_indices:
    print(f"\n--- Przypadek #{idx} ---")
    
    true_cat = y_test[idx]
    pred_cat = y_pred[idx]
    probas = y_pred_proba[idx]
    
    print(f"Prawdziwa kategoria:  {true_cat}")
    print(f"Przewidywana:         {pred_cat}")
    print(f"{'✅ POPRAWNA' if true_cat == pred_cat else '❌ BŁĘDNA'}")
    
    print(f"\nPrawdopodobieństwa:")
    for cat in range(1, 6):
        prob = probas[cat-1] * 100
        bar = "█" * int(prob / 2)
        marker = " ← PRZEWIDYWANA" if cat == pred_cat else ""
        marker += " ← PRAWDZIWA" if cat == true_cat else ""
        print(f"  Kat {cat}: {prob:>5.1f}% {bar}{marker}")

# ============================================================================
# 9. PORÓWNANIE Z POPRZEDNIMI MODELAMI
# ============================================================================
print("\n" + "="*70)
print("PORÓWNANIE Z POPRZEDNIMI MODELAMI")
print("="*70)

print(f"\nModel                    | Accuracy | Balanced Acc")
print(f"-" * 55)
print(f"Random Forest (baseline) |  60.89%  |    ~58%")
print(f"RF + SMOTETomek          |  65.80%  |    69.14%")
print(f"Deep Learning            |  {accuracy:.2%}  |    {balanced_acc:.2%}")

improvement = (accuracy - 0.6089) * 100
print(f"\n📈 Poprawa: +{improvement:.1f} punktów procentowych")

if balanced_acc >= 0.80:
    print(f"\n✅ 🎉 CEL OSIĄGNIĘTY! Balanced Accuracy ≥ 80%")
elif balanced_acc >= 0.75:
    print(f"\n⚠️  Blisko celu! Potrzeba jeszcze +{(0.80-balanced_acc)*100:.1f} pp")
else:
    print(f"\n❌ Cel nie osiągnięty. Potrzebne dalsze ulepszenia.")

print("\n" + "="*70)
print("TEST ZAKOŃCZONY")
print("="*70)
