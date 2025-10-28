import pandas as pd
import pickle
from pathlib import Path
from sklearn.preprocessing import StandardScaler

# Ścieżki
DATA_PATH = Path('/home/dolfik/Projects/Clinic-data/data/processed/')
MODEL_PATH = Path('/home/dolfik/Projects/Clinic-data/models/')

print("📊 Tworzenie scalera dla modelu triaży")
print("=" * 70)

# 1. Wczytaj dane treningowe
print("\n1. Wczytywanie danych treningowych...")
X_train = pd.read_csv(DATA_PATH / 'X_train.csv')
print(f"   ✓ Wczytano {X_train.shape[0]} próbek, {X_train.shape[1]} cech")

# 2. Wybierz dokładnie te kolumny których oczekuje model
expected_features = [
    'wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
    'temperatura', 'saturacja', 'płeć_encoded',
    'godzina', 'dzien_tygodnia', 'miesiac', 'czy_weekend',
    'oddział_Chirurgia', 'oddział_Interna', 'oddział_Kardiologia',
    'oddział_Neurologia', 'oddział_Ortopedia', 'oddział_Pediatria', 'oddział_SOR',
    'szablon_bol_brzucha', 'szablon_bol_w_klatce', 'szablon_infekcja_ukladu_moczowego',
    'szablon_krwawienie_z_przewodu_pokarmowego', 'szablon_migrena', 'szablon_napad_padaczkowy',
    'szablon_omdlenie', 'szablon_reakcja_alergiczna', 'szablon_silne_krwawienie',
    'szablon_udar', 'szablon_uraz_glowy', 'szablon_uraz_wielonarzadowy',
    'szablon_zaburzenia_rytmu_serca', 'szablon_zaostrzenie_astmy', 'szablon_zaostrzenie_pochp',
    'szablon_zapalenie_opon_mozgowych', 'szablon_zapalenie_pluc', 'szablon_zapalenie_wyrostka',
    'szablon_zatrucie_pokarmowe', 'szablon_zlamanie_konczyny'
]

print("\n2. Sprawdzanie dostępności cech...")
missing_features = [f for f in expected_features if f not in X_train.columns]
if missing_features:
    print(f"   ⚠ BRAK cech: {missing_features}")
    print("   Próbuję użyć dostępnych cech...")
    available_features = [f for f in expected_features if f in X_train.columns]
    X_train_selected = X_train[available_features]
else:
    print("   ✓ Wszystkie cechy dostępne")
    X_train_selected = X_train[expected_features]

print(f"   Wybrano {X_train_selected.shape[1]} cech")

# 3. Stwórz i wytrenuj scaler
print("\n3. Trenowanie StandardScaler...")
scaler = StandardScaler()
scaler.fit(X_train_selected)
print("   ✓ Scaler wytrenowany")

# 4. Zapisz scaler
print("\n4. Zapisywanie scalera...")
scaler_path = MODEL_PATH / 'scaler.pkl'
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)

print(f"   ✓ Zapisano: {scaler_path}")

# 5. Test scalera
print("\n5. Test scalera...")
X_scaled = scaler.transform(X_train_selected[:5])
print(f"   Przed skalowaniem (pierwsze 5 wierszy, pierwsze 3 cechy):")
print(X_train_selected.iloc[:5, :3])
print(f"\n   Po skalowaniu:")
print(pd.DataFrame(X_scaled[:, :3], columns=X_train_selected.columns[:3]))

print("\n" + "=" * 70)
print("✅ Scaler gotowy! Zrestartuj backend.")
