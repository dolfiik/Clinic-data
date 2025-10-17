"""
SKRYPT DO POPRAWY GENEROWANIA DANYCH TRIAŻY
Cel: Zwiększenie liczby przykładów dla rzadkich kategorii (4 i 5)

Uruchom PRZED preprocessingiem aby wygenerować lepiej zbalansowane dane
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("="*70)
print("ANALIZA I POPRAWA DANYCH TRIAŻY")
print("="*70)

# ============================================================================
# 1. WCZYTAJ OBECNE DANE
# ============================================================================
data_path = Path('data/raw/triage_data.csv')

if not data_path.exists():
    print(f"\n❌ Plik nie znaleziony: {data_path}")
    print("   Upewnij się, że uruchamiasz skrypt z głównego katalogu projektu")
    exit(1)

df = pd.read_csv(data_path)
print(f"\n✓ Wczytano dane: {len(df)} rekordów")

# ============================================================================
# 2. ANALIZA OBECNEGO ROZKŁADU
# ============================================================================
print("\n" + "="*70)
print("OBECNY ROZKŁAD KATEGORII")
print("="*70)

current_dist = df['kategoria_triażu'].value_counts().sort_index()
total = len(df)

print("\nKategoria | Liczba | Procent | Cel")
print("-" * 50)

target_dist = {1: 0.20, 2: 0.25, 3: 0.25, 4: 0.20, 5: 0.10}

for cat in range(1, 6):
    count = current_dist.get(cat, 0)
    pct = count / total * 100
    target_pct = target_dist[cat] * 100
    target_count = int(total * target_dist[cat])
    diff = count - target_count
    
    status = "✓" if abs(diff) < total * 0.02 else "⚠️"
    print(f"    {cat}     | {count:>5}  | {pct:>5.1f}% | {target_pct:>5.1f}% {status}")

print("\nImbalance ratio:", current_dist.max() / current_dist.min(), "x")

# ============================================================================
# 3. OBLICZ ILE TRZEBA DODAĆ
# ============================================================================
print("\n" + "="*70)
print("PLAN AUGMENTACJI DANYCH")
print("="*70)

# Docelowa wielkość datasetu
target_size = 10000  # Zwiększ z 7500 do 10000

print(f"\nDocelowa wielkość datasetu: {target_size}")
print(f"Obecna wielkość: {len(df)}")
print(f"Dodać: {target_size - len(df)} rekordów")

augmentation_plan = {}
for cat in range(1, 6):
    current = current_dist.get(cat, 0)
    target = int(target_size * target_dist[cat])
    to_add = max(0, target - current)
    augmentation_plan[cat] = to_add
    
    if to_add > 0:
        print(f"\nKategoria {cat}:")
        print(f"  Obecnie:  {current}")
        print(f"  Docelowo: {target}")
        print(f"  Dodać:    {to_add} rekordów")

# ============================================================================
# 4. AUGMENTACJA - TWORZENIE SYNTETYCZNYCH PRZYKŁADÓW
# ============================================================================
print("\n" + "="*70)
print("TWORZENIE SYNTETYCZNYCH PRZYKŁADÓW")
print("="*70)

def augment_category(df, category, n_samples):
    """
    Tworzy syntetyczne przykłady dla danej kategorii
    Metoda: Add small random noise to existing samples
    """
    # Filtruj przykłady z danej kategorii
    cat_samples = df[df['kategoria_triażu'] == category].copy()
    
    if len(cat_samples) == 0:
        print(f"  ⚠️ Brak przykładów dla kategorii {category}")
        return pd.DataFrame()
    
    # Kolumny numeryczne do augmentacji
    numeric_cols = ['wiek', 'tętno', 'ciśnienie_skurczowe', 'ciśnienie_rozkurczowe',
                   'temperatura', 'saturacja']
    
    # Losowo wybierz próbki do duplikacji
    augmented_samples = []
    
    for _ in range(n_samples):
        # Wybierz losową próbkę
        base_sample = cat_samples.sample(n=1).iloc[0].copy()
        
        # Dodaj mały szum do parametrów numerycznych
        for col in numeric_cols:
            if col in base_sample.index and pd.notna(base_sample[col]):
                # Szum: 5-10% wartości
                noise_factor = np.random.uniform(0.05, 0.10)
                noise = np.random.normal(0, base_sample[col] * noise_factor)
                base_sample[col] = base_sample[col] + noise
                
                # Zapewnij rozsądne zakresy
                if col == 'wiek':
                    base_sample[col] = np.clip(base_sample[col], 0, 110)
                elif col == 'tętno':
                    base_sample[col] = np.clip(base_sample[col], 30, 200)
                elif col == 'ciśnienie_skurczowe':
                    base_sample[col] = np.clip(base_sample[col], 60, 250)
                elif col == 'ciśnienie_rozkurczowe':
                    base_sample[col] = np.clip(base_sample[col], 30, 150)
                elif col == 'temperatura':
                    base_sample[col] = np.clip(base_sample[col], 35.0, 42.0)
                elif col == 'saturacja':
                    base_sample[col] = np.clip(base_sample[col], 70, 100)
        
        augmented_samples.append(base_sample)
    
    return pd.DataFrame(augmented_samples)

# Wykonaj augmentację dla każdej kategorii
augmented_dfs = []

for cat, n_to_add in augmentation_plan.items():
    if n_to_add > 0:
        print(f"\n⏳ Augmentacja kategorii {cat}: dodawanie {n_to_add} przykładów...")
        aug_df = augment_category(df, cat, n_to_add)
        
        if len(aug_df) > 0:
            augmented_dfs.append(aug_df)
            print(f"✓ Dodano {len(aug_df)} syntetycznych przykładów")

# ============================================================================
# 5. POŁĄCZ ORYGINALNE I AUGMENTOWANE DANE
# ============================================================================
print("\n" + "="*70)
print("ŁĄCZENIE DANYCH")
print("="*70)

if augmented_dfs:
    df_augmented_only = pd.concat(augmented_dfs, ignore_index=True)
    df_combined = pd.concat([df, df_augmented_only], ignore_index=True)
    
    print(f"\n✓ Oryginalne dane:      {len(df)} rekordów")
    print(f"✓ Augmentowane dane:    {len(df_augmented_only)} rekordów")
    print(f"✓ Łącznie:              {len(df_combined)} rekordów")
else:
    df_combined = df
    print("\n⚠️ Brak danych do augmentacji")

# ============================================================================
# 6. WERYFIKACJA NOWEGO ROZKŁADU
# ============================================================================
print("\n" + "="*70)
print("NOWY ROZKŁAD KATEGORII")
print("="*70)

new_dist = df_combined['kategoria_triażu'].value_counts().sort_index()
total_new = len(df_combined)

print("\nKategoria | Stary  | Nowy   | Cel    | Status")
print("-" * 60)

for cat in range(1, 6):
    old_count = current_dist.get(cat, 0)
    new_count = new_dist.get(cat, 0)
    old_pct = old_count / total * 100
    new_pct = new_count / total_new * 100
    target_pct = target_dist[cat] * 100
    
    diff = abs(new_pct - target_pct)
    status = "✅" if diff < 3 else "⚠️" if diff < 5 else "❌"
    
    print(f"    {cat}     | {old_pct:>5.1f}% | {new_pct:>5.1f}% | {target_pct:>5.1f}% | {status}")

new_imbalance = new_dist.max() / new_dist.min()
old_imbalance = current_dist.max() / current_dist.min()

print(f"\nImbalance ratio:")
print(f"  Przed: {old_imbalance:.2f}x")
print(f"  Po:    {new_imbalance:.2f}x")
print(f"  Poprawa: {old_imbalance - new_imbalance:.2f}x")

# ============================================================================
# 7. ZAPIS ULEPSZONYCH DANYCH
# ============================================================================
print("\n" + "="*70)
print("ZAPIS DANYCH")
print("="*70)

# Zapisz backup oryginalnych danych
backup_path = Path('data/raw/triage_data_original_backup.csv')
if not backup_path.exists():
    df.to_csv(backup_path, index=False)
    print(f"\n✓ Backup oryginalnych danych: {backup_path}")

# Zapisz nowe dane
output_path = Path('data/raw/triage_data.csv')
df_combined.to_csv(output_path, index=False)
print(f"✓ Zapisano ulepszone dane: {output_path}")
print(f"  Liczba rekordów: {len(df_combined)}")

# Zapisz również wersję "improved"
improved_path = Path('data/raw/triage_data_improved.csv')
df_combined.to_csv(improved_path, index=False)
print(f"✓ Zapisano również jako: {improved_path}")

print("\n" + "="*70)
print("✅ AUGMENTACJA ZAKOŃCZONA SUKCESEM!")
print("="*70)
print("\nKolejne kroki:")
print("1. Uruchom ponownie preprocessing notebook (01_EDA_i_przygotowanie_danych.ipynb)")
print("2. Uruchom ulepszone trenowanie: python train_triage_classification_IMPROVED.py")
print("3. Przetestuj model: python test_model.py")
print("\n" + "="*70)
