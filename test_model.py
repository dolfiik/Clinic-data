
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

MODEL_PATH = Path('models/random_forest_20251017_123356.pkl')
DATA_PATH = Path('data/processed/')

print("="*70)
print("TESTOWANIE MODELU KLASYFIKACJI TRIAŻY")
print("="*70)

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)
print(f"✓ Model załadowany: {MODEL_PATH}")

print("\nŁadowanie danych testowych...")
X_test = pd.read_csv(DATA_PATH / 'X_test.csv')
y_test = pd.read_csv(DATA_PATH / 'y_test.csv').values.ravel()

text_columns = X_test.select_dtypes(include=['object']).columns.tolist()
if text_columns:
    X_test = X_test.drop(columns=text_columns)

X_test = X_test.astype(float)

print(f" Dane testowe: {len(X_test)} przypadków")
print(f" Liczba cech: {X_test.shape[1]}")

df_original = pd.read_csv('data/raw/triage_data.csv')
df_original['data_przyjęcia'] = pd.to_datetime(df_original['data_przyjęcia'])

# Wybierz losowe przypadki z każdej kategorii
np.random.seed(42)
test_cases = []

for category in [1, 2, 3, 4, 5]:
    # Znajdź indeksy dla tej kategorii
    indices = np.where(y_test == category)[0]
    if len(indices) > 0:
        # Wybierz losowy przypadek
        idx = np.random.choice(indices)
        test_cases.append((idx, category))

# Przeanalizuj każdy przypadek
for test_idx, true_category in test_cases:
    # Pobierz dane przypadku
    case_features = X_test.iloc[test_idx:test_idx+1]
    
    # Przewidywanie
    prediction = model.predict(case_features)[0]
    probabilities = model.predict_proba(case_features)[0]
    
    # Znajdź odpowiadający wiersz w oryginalnych danych
    # (używamy indeksu z test split)
    
    print(f"\n{'='*70}")
    print(f"PRZYPADEK TESTOWY #{test_idx}")
    print(f"{'='*70}")
    
    # Podstawowe statystyki z cech
    wiek = case_features['wiek'].values[0] if 'wiek' in case_features else "N/A"
    tetno = case_features['tętno'].values[0] if 'tętno' in case_features else "N/A"
    
    print(f"\nParametry (znormalizowane):")
    print(f"  Wiek: {wiek:.2f}" if isinstance(wiek, (int, float)) else f"  Wiek: {wiek}")
    print(f"  Tętno: {tetno:.2f}" if isinstance(tetno, (int, float)) else f"  Tętno: {tetno}")
    
    # Znajdź aktywne cechy one-hot
    active_features = []
    for col in case_features.columns:
        if case_features[col].values[0] > 0.5:  # one-hot encoded
            if col.startswith('szablon_') or col.startswith('oddział_'):
                active_features.append(col.replace('szablon_', '').replace('oddział_', ''))
    
    if active_features:
        print(f"\nAktywne cechy: {', '.join(active_features[:3])}")
    
    print(f"\n{'─'*70}")
    print(f"PRAWDZIWA kategoria triaży:    {int(true_category)}")
    print(f"PRZEWIDYWANA kategoria triaży: {int(prediction)}")
    
    # Sprawdź czy poprawnie
    if int(prediction) == int(true_category):
        print(" POPRAWNA PREDYKCJA")
    else:
        print(" BŁĘDNA PREDYKCJA")
    
    print(f"\nPrawdopodobieństwa dla każdej kategorii:")
    for i, prob in enumerate(probabilities, 1):
        bar = '█' * int(prob * 50)
        marker = " ← PRZEWIDYWANA" if i == prediction else ""
        marker += " ← PRAWDZIWA" if i == true_category else ""
        print(f"  Kategoria {i}: {prob:6.2%} {bar}{marker}")



all_predictions = model.predict(X_test)

# Accuracy
accuracy = np.mean(all_predictions == y_test)
print(f"\nDokładność (Accuracy): {accuracy:.2%}")

# Macierz pomyłek (confusion matrix) - uproszczona
print(f"\nRozkład predykcji vs prawdziwe wartości:")
print(f"{'Prawdziwa':<12} {'Poprawne':<10} {'Błędne':<10} {'Dokładność':<12}")
print("-" * 50)

for category in [1, 2, 3, 4, 5]:
    mask = y_test == category
    if np.sum(mask) > 0:
        correct = np.sum((all_predictions == category) & mask)
        total = np.sum(mask)
        incorrect = total - correct
        cat_accuracy = correct / total
        print(f"Kategoria {category}  {correct:<10} {incorrect:<10} {cat_accuracy:>10.1%}")

# Sprawdź czy model preferuje jakąś kategorię
print(f"\nRozkład przewidywanych kategorii:")
unique, counts = np.unique(all_predictions, return_counts=True)
for cat, count in zip(unique, counts):
    pct = count / len(all_predictions) * 100
    bar = '█' * int(pct / 2)
    print(f"  Kategoria {int(cat)}: {count:>4} ({pct:>5.1f}%) {bar}")

print(f"\nRozkład prawdziwych kategorii:")
unique, counts = np.unique(y_test, return_counts=True)
for cat, count in zip(unique, counts):
    pct = count / len(y_test) * 100
    bar = '█' * int(pct / 2)
    print(f"  Kategoria {int(cat)}: {count:>4} ({pct:>5.1f}%) {bar}")

print("\n" + "="*70)
print("WYSZUKIWANIE PRZYPADKÓW")
print("="*70)

print("\nChcesz sprawdzić konkretny przypadek z zestawu testowego?")
print("Podaj numer indeksu (0-{}), lub naciśnij Enter aby pominąć: ".format(len(X_test)-1), end='')

user_input = input().strip()
if user_input:
    try:
        idx = int(user_input)
        if 0 <= idx < len(X_test):
            case_features = X_test.iloc[idx:idx+1]
            true_cat = y_test[idx]
            pred_cat = model.predict(case_features)[0]
            probs = model.predict_proba(case_features)[0]
            
            print(f"\n{'='*70}")
            print(f"PRZYPADEK #{idx}")
            print(f"{'='*70}")
            print(f"Prawdziwa kategoria: {int(true_cat)}")
            print(f"Przewidywana kategoria: {int(pred_cat)}")
            print(f"\nPrawdopodobieństwa:")
            for i, prob in enumerate(probs, 1):
                bar = '█' * int(prob * 50)
                print(f"  Kategoria {i}: {prob:6.2%} {bar}")
        else:
            print(f"Błąd: Indeks poza zakresem (0-{len(X_test)-1})")
    except ValueError:
        print("Błąd: Nieprawidłowy indeks")

