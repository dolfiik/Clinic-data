import pandas as pd
import pickle
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from datetime import datetime

print("🔧 ODTWARZANIE SCALERA Z SUROWYCH DANYCH")
print("=" * 70)

# Ścieżki
RAW_DATA = Path('/home/dolfik/Projects/Clinic-data/data/raw/triage_data.csv')
PROCESSED_TRAIN = Path('/home/dolfik/Projects/Clinic-data/data/processed/X_train.csv')
MODEL_PATH = Path('/home/dolfik/Projects/Clinic-data/models/')

# 1. Wczytaj surowe dane
print("\n1. Wczytywanie surowych danych...")
df_raw = pd.read_csv(RAW_DATA)
print(f"   ✓ Wczytano {len(df_raw)} rekordów")
print(f"   Kolumny: {list(df_raw.columns)}")

# 2. Wczytaj przetworzone dane żeby zobaczyć strukturę
print("\n2. Sprawdzanie struktury przetworzonych danych...")
X_train = pd.read_csv(PROCESSED_TRAIN)
print(f"   ✓ Cechy w X_train: {X_train.shape[1]}")
print(f"   Kolumny: {list(X_train.columns)[:10]}...")

# 3. Preprocessing surowych danych
print("\n3. Preprocessing surowych danych...")

# Wybierz cechy numeryczne
numerical_cols = ['wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe', 
                  'temperatura', 'saturacja']

df_processed = df_raw[numerical_cols].copy()

# One-hot encoding płci
df_processed['płeć_encoded'] = (df_raw['płeć'] == 'M').astype(int)

# Cechy datetime
df_processed['data_przyjęcia'] = pd.to_datetime(df_raw['data_przyjęcia'])
df_processed['godzina'] = df_processed['data_przyjęcia'].dt.hour
df_processed['dzien_tygodnia'] = df_processed['data_przyjęcia'].dt.dayofweek
df_processed['miesiac'] = df_processed['data_przyjęcia'].dt.month
df_processed['czy_weekend'] = (df_processed['dzien_tygodnia'] >= 5).astype(int)
df_processed = df_processed.drop('data_przyjęcia', axis=1)

# One-hot encoding oddziałów
departments = ['Chirurgia', 'Interna', 'Kardiologia', 'Neurologia', 'Ortopedia', 'SOR']
for dept in departments:
    df_processed[f'oddział_{dept}'] = (df_raw['oddział_docelowy'] == dept).astype(int)

# One-hot encoding szablonów (użyj DOKŁADNIE tych z X_train)
template_cols = [col for col in X_train.columns if col.startswith('szablon_')]
print(f"\n   Szablony w X_train: {len(template_cols)}")
for template_col in template_cols:
    df_processed[template_col] = 0  # Wszystkie na 0 domyślnie

# Ustaw odpowiednie szablony na 1
for idx, szablon in enumerate(df_raw['szablon_przypadku']):
    col_name = f'szablon_{szablon}'
    if col_name in df_processed.columns:
        df_processed.loc[idx, col_name] = 1

print(f"   ✓ Preprocessed shape: {df_processed.shape}")

# 4. Upewnij się że kolejność kolumn jest taka sama jak w X_train
print("\n4. Dopasowanie kolejności kolumn...")
missing_in_processed = set(X_train.columns) - set(df_processed.columns)
extra_in_processed = set(df_processed.columns) - set(X_train.columns)

if missing_in_processed:
    print(f"   ⚠ Brakujące kolumny: {missing_in_processed}")
    for col in missing_in_processed:
        df_processed[col] = 0

if extra_in_processed:
    print(f"   Usuwam nadmiarowe kolumny: {extra_in_processed}")
    df_processed = df_processed.drop(columns=list(extra_in_processed))

# Ustaw tę samą kolejność co X_train
df_processed = df_processed[X_train.columns]
print(f"   ✓ Dopasowano kolejność - shape: {df_processed.shape}")

# 5. Trenuj scaler
print("\n5. Trenowanie StandardScaler...")
scaler = StandardScaler()
scaler.fit(df_processed)
print("   ✓ Scaler wytrenowany")

# 6. Sprawdź czy scaler działa poprawnie
print("\n6. Weryfikacja scalera...")
X_scaled = scaler.transform(df_processed[:5])
print(f"   Przed skalowaniem (pierwsze 3 cechy):")
print(df_processed[['wiek', 'tętno', 'ciśnienie_skurczowe']].head())
print(f"\n   Po skalowaniu:")
print(pd.DataFrame(X_scaled[:, :3], columns=['wiek', 'tętno', 'ciśnienie_skurczowe']))

# Porównaj z X_train
print(f"\n   X_train (pierwsze 3 cechy, pierwsze 5 wierszy):")
print(X_train[['wiek', 'tętno', 'ciśnienie_skurczowe']].head())

# 7. Zapisz scaler
print("\n7. Zapisywanie scalera...")
scaler_path = MODEL_PATH / 'scaler.pkl'
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"   ✓ Zapisano: {scaler_path}")

print("\n" + "=" * 70)
print("✅ GOTOWE! Zrestartuj backend i testuj model.")
