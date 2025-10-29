"""
Skrypt wyciąga DOKŁADNE cechy których model oczekuje
Uruchom: python extract_model_features.py
"""

import sys
import pickle
from pathlib import Path

# Możliwe lokalizacje modelu
possible_paths = [
"/home/dolfik/Projects/Clinic-data/models/ensemble_(weighted)_improved_20251029_081659.pkl"
]

print("=" * 80)
print("EKSTRAKCJA CECH Z WYTRENOWANEGO MODELU")
print("=" * 80)

model = None
model_path = None

# Szukaj modelu
for path in possible_paths:
    p = Path(path)
    if p.exists():
        print(f"\n✓ Znaleziono model: {path}")
        model_path = p
        try:
            with open(p, 'rb') as f:
                model = pickle.load(f)
            break
        except Exception as e:
            print(f"  ✗ Błąd wczytywania: {e}")
            continue

if model is None:
    print("\n❌ NIE ZNALEZIONO MODELU!")
    print("\nPodaj ścieżkę do modelu:")
    user_path = input("Ścieżka: ").strip()
    if user_path:
        try:
            with open(user_path, 'rb') as f:
                model = pickle.load(f)
            model_path = Path(user_path)
        except Exception as e:
            print(f"❌ Błąd: {e}")
            sys.exit(1)
    else:
        print("❌ Brak modelu. Kończę.")
        sys.exit(1)

print(f"\n✓ Model wczytany z: {model_path}")
print(f"  Typ: {type(model).__name__}")

# Wyciągnij cechy
if hasattr(model, 'feature_names_in_'):
    features = model.feature_names_in_
    print(f"\n✓ Model ma {len(features)} cech")
    
    # Kategoryzuj cechy
    numerical = []
    gender = []
    datetime_feats = []
    departments = []
    templates = []
    other = []
    
    for feat in features:
        if feat.startswith('szablon_'):
            templates.append(feat.replace('szablon_', ''))
        elif feat.startswith('oddział_'):
            departments.append(feat.replace('oddział_', ''))
        elif feat in ['wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe', 
                      'temperatura', 'saturacja']:
            numerical.append(feat)
        elif feat == 'płeć_encoded':
            gender.append(feat)
        elif feat in ['godzina', 'dzien_tygodnia', 'miesiac', 'czy_weekend']:
            datetime_feats.append(feat)
        else:
            other.append(feat)
    
    # Wyświetl wyniki
    print("\n" + "=" * 80)
    print("CECHY NUMERYCZNE:")
    print("=" * 80)
    for feat in numerical:
        print(f"  - {feat}")
    
    print("\n" + "=" * 80)
    print("PŁEĆ:")
    print("=" * 80)
    for feat in gender:
        print(f"  - {feat}")
    
    print("\n" + "=" * 80)
    print("CECHY CZASOWE:")
    print("=" * 80)
    for feat in datetime_feats:
        print(f"  - {feat}")
    
    print("\n" + "=" * 80)
    print(f"ODDZIAŁY ({len(departments)}):")
    print("=" * 80)
    for dept in sorted(departments):
        print(f"  - {dept}")
    
    print("\n" + "=" * 80)
    print(f"SZABLONY ({len(templates)}):")
    print("=" * 80)
    for tmpl in sorted(templates):
        print(f"  - {tmpl}")
    
    if other:
        print("\n" + "=" * 80)
        print("INNE CECHY:")
        print("=" * 80)
        for feat in other:
            print(f"  - {feat}")
    
    # Wygeneruj kod Python
    print("\n" + "=" * 80)
    print("KOD DO SKOPIOWANIA DO PREPROCESSORA:")
    print("=" * 80)
    
    print("\n# Lista oddziałów (DOKŁADNA z modelu):")
    print("self.departments = [")
    for dept in sorted(departments):
        print(f"    '{dept}',")
    print("]")
    
    print("\n# Lista szablonów (DOKŁADNA z modelu):")
    print("self.templates = [")
    for tmpl in sorted(templates):
        print(f"    '{tmpl}',")
    print("]")
    
    # Zapisz do pliku
    output_file = Path('model_features.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("CECHY MODELU\n")
        f.write("=" * 80 + "\n\n")
        f.write("ODDZIAŁY:\n")
        for dept in sorted(departments):
            f.write(f"  - {dept}\n")
        f.write("\nSZABLONY:\n")
        for tmpl in sorted(templates):
            f.write(f"  - {tmpl}\n")
        f.write("\nWszystkie cechy po kolei:\n")
        for feat in features:
            f.write(f"  - {feat}\n")
    
    print(f"\n✓ Zapisano szczegóły do: {output_file.absolute()}")
    
else:
    print("\n❌ Model nie ma atrybutu 'feature_names_in_'")
    print("   Model może być starszej wersji sklearn")

print("\n" + "=" * 80)
