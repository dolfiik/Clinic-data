# ============================================================================
# POPRAWIONY NOTEBOOK - PREPROCESSING DANYCH TRIAŻY
# Zachowuje WSZYSTKIE 7500 rekordów zamiast tylko 1500
# ============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os

# Konfiguracja
warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.2f' % x)

print("="*70)
print("POPRAWIONY PREPROCESSING - ZACHOWUJE WSZYSTKIE DANE")
print("="*70)

# ============================================================================
# 1. WCZYTANIE DANYCH
# ============================================================================
TRIAGE_DATA_PATH = '../../raw/triage_data.csv'

df_triage = pd.read_csv(TRIAGE_DATA_PATH)
print(f"\n✓ Wczytano dane: {df_triage.shape[0]} wierszy × {df_triage.shape[1]} kolumn")
print(f"  Początkowa liczba rekordów: {len(df_triage)}")

# ============================================================================
# 2. SPRAWDZENIE BRAKUJĄCYCH WARTOŚCI
# ============================================================================
print("\n" + "="*70)
print("ANALIZA BRAKUJĄCYCH WARTOŚCI")
print("="*70)

missing = df_triage.isnull().sum()
missing_pct = (missing / len(df_triage)) * 100
missing_df = pd.DataFrame({
    'Kolumna': missing.index,
    'Brakujące': missing.values,
    'Procent': missing_pct.values
}).sort_values('Brakujące', ascending=False)

print("\nKolumny z brakującymi wartościami:")
print(missing_df[missing_df['Brakujące'] > 0])

# ============================================================================
# 3. PRZYGOTOWANIE DANYCH - BEZ USUWANIA WIERSZY!
# ============================================================================
print("\n" + "="*70)
print("PRZYGOTOWANIE DANYCH (BEZ USUWANIA WIERSZY)")
print("="*70)

df_model = df_triage.copy()

# Konwersja daty
df_model['data_przyjęcia'] = pd.to_datetime(df_model['data_przyjęcia'])

# Ekstrakcja cech czasowych
df_model['godzina'] = df_model['data_przyjęcia'].dt.hour
df_model['dzien_tygodnia'] = df_model['data_przyjęcia'].dt.dayofweek
df_model['miesiac'] = df_model['data_przyjęcia'].dt.month
df_model['czy_weekend'] = df_model['dzien_tygodnia'].isin([5, 6]).astype(int)

print("✓ Cechy czasowe utworzone")

# ============================================================================
# 4. WYPEŁNIANIE BRAKUJĄCYCH WARTOŚCI (zamiast dropna!)
# ============================================================================
print("\n--- Wypełnianie brakujących wartości ---")

# Lista parametrów numerycznych
numeric_features = ['wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
                   'temperatura', 'saturacja']

# Wypełnij brakujące wartości MEDIANĄ (bardziej odporne na outliers)
for col in numeric_features:
    if col in df_model.columns:
        missing_count = df_model[col].isnull().sum()
        if missing_count > 0:
            median_val = df_model[col].median()
            df_model[col].fillna(median_val, inplace=True)
            print(f"  {col}: wypełniono {missing_count} wartości medianą ({median_val:.2f})")

# Wypełnij brakujące wartości kategoryczne najczęstszą wartością
categorical_cols = ['płeć', 'oddział_docelowy', 'szablon_przypadku']
for col in categorical_cols:
    if col in df_model.columns:
        missing_count = df_model[col].isnull().sum()
        if missing_count > 0:
            mode_val = df_model[col].mode()[0]
            df_model[col].fillna(mode_val, inplace=True)
            print(f"  {col}: wypełniono {missing_count} wartości wartością '{mode_val}'")

print(f"\n✓ Po wypełnieniu: {len(df_model)} rekordów (żadne nie usunięte!)")

# ============================================================================
# 5. KODOWANIE ZMIENNYCH KATEGORYCZNYCH
# ============================================================================
print("\n--- Kodowanie zmiennych kategorycznych ---")

# Label encoding dla płci
df_model['płeć_encoded'] = df_model['płeć'].map({'M': 1, 'K': 0})

# One-hot encoding dla oddziałów
dept_dummies = pd.get_dummies(df_model['oddział_docelowy'], prefix='oddział')
df_model = pd.concat([df_model, dept_dummies], axis=1)

# One-hot encoding dla szablonów przypadków
template_dummies = pd.get_dummies(df_model['szablon_przypadku'], prefix='szablon')
df_model = pd.concat([df_model, template_dummies], axis=1)

print(f"✓ Zmienne zakodowane")
print(f"  Kolumny oddziałów: {len([c for c in dept_dummies.columns])}")
print(f"  Kolumny szablonów: {len([c for c in template_dummies.columns])}")
print(f"  Łączna liczba kolumn: {df_model.shape[1]}")

# ============================================================================
# 6. SELEKCJA CECH
# ============================================================================
print("\n--- Selekcja cech ---")

# Cechy numeryczne + czasowe
base_features = ['wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
                'temperatura', 'saturacja', 'płeć_encoded', 
                'godzina', 'dzien_tygodnia', 'miesiac', 'czy_weekend']

# Dodanie cech dummy
dept_cols = [col for col in df_model.columns if col.startswith('oddział_')]
template_cols = [col for col in df_model.columns if col.startswith('szablon_')]

all_features = base_features + dept_cols + template_cols

print(f"  Cechy bazowe: {len(base_features)}")
print(f"  Cechy oddziałów: {len(dept_cols)}")
print(f"  Cechy szablonów: {len(template_cols)}")
print(f"  Łącznie cech: {len(all_features)}")

# KRYTYCZNE: Sprawdź czy są jeszcze NaN (nie powinno być!)
df_model_features = df_model[all_features + ['kategoria_triażu']]
remaining_nan = df_model_features.isnull().sum().sum()

if remaining_nan > 0:
    print(f"\n⚠️  UWAGA: Pozostało {remaining_nan} wartości NaN!")
    print("Wypełnianie zerami...")
    df_model_features = df_model_features.fillna(0)
else:
    print(f"\n✓ Brak wartości NaN - dane kompletne!")

print(f"✓ Finalna liczba rekordów: {len(df_model_features)} (zachowano 100%!)")

# ============================================================================
# 7. NORMALIZACJA
# ============================================================================
print("\n--- Normalizacja cech numerycznych ---")

scaler = StandardScaler()
df_model_features[base_features] = scaler.fit_transform(df_model_features[base_features])
print("✓ Cechy numeryczne znormalizowane (StandardScaler)")

# ============================================================================
# 8. PODZIAŁ NA X i y
# ============================================================================
X = df_model_features[all_features]
y = df_model_features['kategoria_triażu']

print(f"\n--- Przygotowane dane ---")
print(f"  X shape: {X.shape}")
print(f"  y shape: {y.shape}")
print(f"  Liczba rekordów: {len(X)}")

# Sprawdzenie balansu klas
print(f"\n  Rozkład klas:")
class_counts = y.value_counts().sort_index()
for cat, count in class_counts.items():
    pct = count / len(y) * 100
    print(f"    Kategoria {cat}: {count:>4} ({pct:>5.1f}%)")

# ============================================================================
# 9. PODZIAŁ NA TRAIN/VAL/TEST
# ============================================================================
print("\n" + "="*70)
print("PODZIAŁ DANYCH: 70% TRAIN / 15% VAL / 15% TEST")
print("="*70)

# Krok 1: Oddziel 15% na test
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)

# Krok 2: Z pozostałych 85% oddziel ~17.65% na walidację (15% z całości)
# 15% / 85% ≈ 0.1765
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.1765, random_state=42, stratify=y_temp
)

print(f"\n✅ PODZIAŁ ZAKOŃCZONY:")
print(f"  Treningowy: {X_train.shape[0]:>4} próbek ({X_train.shape[0]/len(X)*100:>5.1f}%)")
print(f"  Walidacyjny: {X_val.shape[0]:>4} próbek ({X_val.shape[0]/len(X)*100:>5.1f}%)")
print(f"  Testowy:    {X_test.shape[0]:>4} próbek ({X_test.shape[0]/len(X)*100:>5.1f}%)")
print(f"  RAZEM:      {X_train.shape[0] + X_val.shape[0] + X_test.shape[0]:>4} próbek")

# Weryfikacja balansu klas w każdym zbiorze
print("\n--- Rozkład klas w zbiorach ---")
for name, y_split in [("Treningowy", y_train), ("Walidacyjny", y_val), ("Testowy", y_test)]:
    print(f"\n{name}:")
    counts = y_split.value_counts().sort_index()
    for cat, count in counts.items():
        pct = count / len(y_split) * 100
        print(f"  Kategoria {cat}: {count:>3} ({pct:>5.1f}%)")

# ============================================================================
# 10. EKSPORT DANYCH
# ============================================================================
print("\n" + "="*70)
print("EKSPORT DANYCH")
print("="*70)

# Stwórz folder jeśli nie istnieje
output_dir = '/home/dolfik/Projects/Clinic-data/data/processed/'
os.makedirs(output_dir, exist_ok=True)

# Zapisz wszystkie pliki
df_model_features.to_csv(f'{output_dir}prepared_data.csv', index=False)
X_train.to_csv(f'{output_dir}X_train.csv', index=False)
X_val.to_csv(f'{output_dir}X_val.csv', index=False)
X_test.to_csv(f'{output_dir}X_test.csv', index=False)
y_train.to_csv(f'{output_dir}y_train.csv', index=False)
y_val.to_csv(f'{output_dir}y_val.csv', index=False)
y_test.to_csv(f'{output_dir}y_test.csv', index=False)

print("\n✓ Dane zapisane w folderze 'data/processed/':")
print("  - prepared_data.csv")
print("  - X_train.csv, X_val.csv, X_test.csv")
print("  - y_train.csv, y_val.csv, y_test.csv")

