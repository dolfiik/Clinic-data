import pickle
import pandas as pd
from pathlib import Path

MODEL_PATH = Path('/home/dolfik/Projects/Clinic-data/models/')

print("🚨 TEST EKSTREMALNIE KRYTYCZNEGO PACJENTA")
print("=" * 70)

# Załaduj model
model_file = MODEL_PATH / 'random_forest_improved_20251017_130823.pkl'
with open(model_file, 'rb') as f:
    model = pickle.load(f)

# EKSTREMALNIE KRYTYCZNY - wstrząs kardiogenny
extreme_critical = {
    'wiek': 75.0,
    'tętno': 150.0,           # ⚠️ Bardzo szybkie
    'ciśnienie_skurczowe': 70.0,  # ⚠️ Bardzo niskie (wstrząs!)
    'ciśnienie_rozkurczowe': 40.0,
    'temperatura': 35.5,      # ⚠️ Hipotermia
    'saturacja': 80.0,        # ⚠️ Ciężka hipoksja
    'płeć_encoded': 1.0,
    'godzina': 3.0,           # W nocy
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
    'szablon_bol_w_klatce': 1.0,
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

df = pd.DataFrame([extreme_critical])

print("\n📋 PARAMETRY ŻYCIOWE:")
print(f"   Wiek: {extreme_critical['wiek']:.0f} lat")
print(f"   Tętno: {extreme_critical['tętno']:.0f} bpm  ⚠️ TACHYKARDIA")
print(f"   Ciśnienie: {extreme_critical['ciśnienie_skurczowe']:.0f}/{extreme_critical['ciśnienie_rozkurczowe']:.0f} mmHg  ⚠️ WSTRZĄS")
print(f"   Temperatura: {extreme_critical['temperatura']:.1f}°C  ⚠️ HIPOTERMIA")
print(f"   Saturacja: {extreme_critical['saturacja']:.0f}%  ⚠️ CIĘŻKA HIPOKSJA")
print(f"   Szablon: Ból w klatce piersiowej")

category = model.predict(df)[0]
probs = model.predict_proba(df)[0]

print(f"\n🎯 PREDYKCJA MODELU:")
print(f"   Kategoria: {int(category)}")
print(f"   Pewność: {max(probs):.2%}")
print(f"\n   Rozkład prawdopodobieństw:")
for i, prob in enumerate(probs, 1):
    bar = "█" * int(prob * 50)
    label = ["🔴 NATYCHMIASTOWY", "🟠 PILNY", "🟡 STABILNY", "🟢 NISKI", "⚪ BARDZO NISKI"][i-1]
    print(f"     Kat. {i} {label}: {prob:6.2%} {bar}")

# Test z silnym krwawieniem
print("\n" + "=" * 70)
print("\n🩸 TEST: SILNE KRWAWIENIE")

bleeding = extreme_critical.copy()
bleeding.update({
    'tętno': 140.0,
    'ciśnienie_skurczowe': 80.0,
    'ciśnienie_rozkurczowe': 50.0,
    'szablon_bol_w_klatce': 0.0,
    'szablon_silne_krwawienie': 1.0
})

df_bleeding = pd.DataFrame([bleeding])
cat_bleed = model.predict(df_bleeding)[0]
prob_bleed = model.predict_proba(df_bleeding)[0]

print(f"\n   Kategoria: {int(cat_bleed)}")
print(f"   Rozkład:")
for i, prob in enumerate(prob_bleed, 1):
    bar = "█" * int(prob * 50)
    print(f"     Kat. {i}: {prob:6.2%} {bar}")

# Test z urazem wielonarządowym
print("\n" + "=" * 70)
print("\n💥 TEST: URAZ WIELONARZĄDOWY")

trauma = extreme_critical.copy()
trauma.update({
    'wiek': 25.0,
    'szablon_bol_w_klatce': 0.0,
    'szablon_uraz_wielonarzadowy': 1.0
})

df_trauma = pd.DataFrame([trauma])
cat_trauma = model.predict(df_trauma)[0]
prob_trauma = model.predict_proba(df_trauma)[0]

print(f"\n   Kategoria: {int(cat_trauma)}")
print(f"   Rozkład:")
for i, prob in enumerate(prob_trauma, 1):
    bar = "█" * int(prob * 50)
    print(f"     Kat. {i}: {prob:6.2%} {bar}")

print("\n" + "=" * 70)
print("\n💡 DIAGNOZA:")
if category > 2:
    print("   ⚠️ MODEL MA PROBLEM!")
    print("   Ekstremalnie krytyczny pacjent nie dostaje kategorii 1-2")
    print("   Model prawdopodobnie:")
    print("   1. Został źle wytrenowany")
    print("   2. Ma zbyt niską wagę dla parametrów życiowych")
    print("   3. Dane treningowe były źle oznaczone")
    print("\n   REKOMENDACJA: Przetrenuj model z lepszymi danymi")
else:
    print("   ✓ Model działa poprawnie dla ekstremalnych przypadków")
