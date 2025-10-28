import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

MODEL_PATH = Path('/home/dolfik/Projects/Clinic-data/models/')

print("🧪 BEZPOŚREDNI TEST MODELU")
print("=" * 70)

# 1. Załaduj model
print("\n1. Ładowanie modelu...")
model_file = MODEL_PATH / 'random_forest_improved_20251017_130823.pkl'
with open(model_file, 'rb') as f:
    model = pickle.load(f)
print(f"   ✓ Model załadowany: {type(model).__name__}")

# 2. Przygotuj dane testowe - KRYTYCZNY PACJENT
print("\n2. Przygotowanie danych KRYTYCZNEGO pacjenta...")
critical_patient = {
    'wiek': 68.0,
    'tętno': 125.0,
    'ciśnienie_skurczowe': 85.0,
    'ciśnienie_rozkurczowe': 50.0,
    'temperatura': 38.9,
    'saturacja': 89.0,
    'płeć_encoded': 0.0,  # Kobieta
    'godzina': 19.0,
    'dzien_tygodnia': 1.0,
    'miesiac': 10.0,
    'czy_weekend': 0.0,
    'oddział_Chirurgia': 0.0,
    'oddział_Interna': 0.0,
    'oddział_Kardiologia': 0.0,
    'oddział_Neurologia': 0.0,
    'oddział_Ortopedia': 0.0,
    'oddział_Pediatria': 0.0,
    'oddział_SOR': 0.0,
    'szablon_bol_brzucha': 0.0,
    'szablon_bol_w_klatce': 1.0,  # ✅
    'szablon_infekcja_ukladu_moczowego': 0.0,
    'szablon_krwawienie_z_przewodu_pokarmowego': 0.0,
    'szablon_migrena': 0.0,
    'szablon_napad_padaczkowy': 0.0,
    'szablon_omdlenie': 0.0,
    'szablon_reakcja_alergiczna': 0.0,
    'szablon_silne_krwawienie': 0.0,
    'szablon_udar': 0.0,
    'szablon_uraz_glowy': 0.0,
    'szablon_uraz_wielonarzadowy': 0.0,
    'szablon_zaburzenia_rytmu_serca': 0.0,
    'szablon_zaostrzenie_astmy': 0.0,
    'szablon_zaostrzenie_pochp': 0.0,
    'szablon_zapalenie_opon_mozgowych': 0.0,
    'szablon_zapalenie_pluc': 0.0,
    'szablon_zapalenie_wyrostka': 0.0,
    'szablon_zatrucie_pokarmowe': 0.0,
    'szablon_zlamanie_konczyny': 0.0
}

df = pd.DataFrame([critical_patient])
print(f"   ✓ Shape: {df.shape}")
print(f"   Parametry życiowe:")
print(f"     Wiek: {critical_patient['wiek']:.0f}")
print(f"     Tętno: {critical_patient['tętno']:.0f}")
print(f"     Ciśnienie: {critical_patient['ciśnienie_skurczowe']:.0f}/{critical_patient['ciśnienie_rozkurczowe']:.0f}")
print(f"     Saturacja: {critical_patient['saturacja']:.0f}%")
print(f"     Szablon: bol_w_klatce")

# 3. Predykcja
print("\n3. Wykonywanie predykcji...")
category = model.predict(df)[0]
probabilities = model.predict_proba(df)[0]

print(f"\n   🎯 WYNIK:")
print(f"   Kategoria: {int(category)}")
print(f"   Pewność: {max(probabilities):.2%}")
print(f"\n   Wszystkie prawdopodobieństwa:")
for i, prob in enumerate(probabilities, 1):
    bar = "█" * int(prob * 50)
    print(f"     Kat. {i}: {prob:.2%} {bar}")

# 4. Test ze STABILNYM pacjentem
print("\n" + "=" * 70)
print("\n4. Test ze STABILNYM pacjentem...")

stable_patient = critical_patient.copy()
stable_patient.update({
    'wiek': 30.0,
    'tętno': 70.0,
    'ciśnienie_skurczowe': 120.0,
    'ciśnienie_rozkurczowe': 80.0,
    'temperatura': 36.6,
    'saturacja': 98.0,
    'szablon_bol_w_klatce': 0.0,
    'szablon_bol_brzucha': 1.0
})

df_stable = pd.DataFrame([stable_patient])
print(f"   Parametry życiowe:")
print(f"     Wiek: {stable_patient['wiek']:.0f}")
print(f"     Tętno: {stable_patient['tętno']:.0f}")
print(f"     Ciśnienie: {stable_patient['ciśnienie_skurczowe']:.0f}/{stable_patient['ciśnienie_rozkurczowe']:.0f}")
print(f"     Saturacja: {stable_patient['saturacja']:.0f}%")
print(f"     Szablon: bol_brzucha")

category_stable = model.predict(df_stable)[0]
probs_stable = model.predict_proba(df_stable)[0]

print(f"\n   🎯 WYNIK:")
print(f"   Kategoria: {int(category_stable)}")
print(f"   Pewność: {max(probs_stable):.2%}")
print(f"\n   Wszystkie prawdopodobieństwa:")
for i, prob in enumerate(probs_stable, 1):
    bar = "█" * int(prob * 50)
    print(f"     Kat. {i}: {prob:.2%} {bar}")

print("\n" + "=" * 70)
print("\n💡 WNIOSKI:")
if category == category_stable:
    print("   ⚠️ Model zwraca tę samą kategorię dla obu pacjentów!")
    print("   Problem jest w samym modelu - trzeba go przetrenować.")
else:
    print("   ✓ Model rozróżnia pacjentów poprawnie.")
    print("   Problem jest w preprocessing lub integracji.")
