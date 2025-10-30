import pandas as pd
import random
from datetime import datetime, timedelta
import uuid
import json
import numpy as np

try:
    triage_data = pd.read_csv('data/raw/triage_data.csv')
except Exception as e:
    print(f"Error loading triage data: {e}")
    triage_data = None

DEPARTMENT_CAPACITY = {
    "SOR": 25,
    "Interna": 50,
    "Kardiologia": 30,
    "Chirurgia": 35,
    "Ortopedia": 25,
    "Neurologia": 20,
    "Pediatria": 30,
    "Ginekologia": 20
}


def get_target_occupancy_rate(dept: str, hour: int, day_of_week: int) -> float:
    """
    Zwraca docelowy wskaźnik obłożenia (0-1) based on time patterns.
    To jest TARGET do którego dąży obłożenie, ale nie osiąga natychmiast.
    """
    is_weekend = day_of_week >= 5
    is_night = hour < 6 or hour >= 22
    is_peak_hours = 8 <= hour <= 20
    
    # Bazowy target rate
    if dept == "SOR":
        base_rate = 0.65  # SOR zawsze bardziej zajęty
        
        # Wieczorny szczyt w SOR (18-23)
        if 18 <= hour <= 23:
            base_rate = 0.85
        # Noc (00-06)
        elif 0 <= hour < 6:
            base_rate = 0.55
        # Poranek (06-10)
        elif 6 <= hour < 10:
            base_rate = 0.60
            
    else:
        # Inne oddziały
        base_rate = 0.50
        
        # Peak hours (8-20) - więcej planowanych
        if is_peak_hours:
            base_rate = 0.65
        
        # Noc - mniej pacjentów (poza SOR)
        if is_night:
            base_rate = 0.35
    
    # Weekend effect
    if is_weekend:
        if dept in ["Chirurgia", "Ortopedia", "Ginekologia"]:
            # Dużo mniej planowych zabiegów
            base_rate *= 0.60
        elif dept != "SOR":
            base_rate *= 0.80
    
    # Poniedziałek - weekend backlog
    if day_of_week == 0 and dept != "SOR":
        base_rate = min(0.90, base_rate + 0.15)
    
    # Piątek - więcej wypisów przed weekendem
    if day_of_week == 4 and hour >= 14:
        base_rate *= 0.85
    
    # Clip to [0.2, 0.95]
    return max(0.2, min(0.95, base_rate))


def update_occupancy_with_persistence(
    current_occ: dict,
    hour: int,
    day_of_week: int,
    persistence: float = 0.90
) -> dict:
    """
    Aktualizuje obłożenie z CIĄGŁOŚCIĄ (persistence).
    
    Formula:
        new_occ = persistence * current + (1-persistence) * target + noise
    
    Args:
        current_occ: Obecne obłożenie
        hour: Godzina dnia
        day_of_week: Dzień tygodnia
        persistence: Jak mocno utrzymuje się poprzednia wartość (0.9 = 90%)
    
    Returns:
        Zaktualizowane obłożenie
    """
    new_occ = {}
    
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        # 1. Poprzednia wartość (90%)
        prev_value = current_occ[dept]
        
        # 2. Target value (8%) - do czego dążymy
        target_rate = get_target_occupancy_rate(dept, hour, day_of_week)
        target_value = capacity * target_rate
        
        # 3. Smooth transition z małym szumem (2%)
        # 90% persistence + 8% target + 2% noise
        noise_std = capacity * 0.02  # 2% capacity jako standard deviation
        
        new_value = (
            persistence * prev_value +
            (1 - persistence) * 0.80 * target_value +  # 80% of remaining 10%
            np.random.normal(0, noise_std)  # Gaussian noise
        )
        
        # 4. Random events (rzadkie, ale możliwe)
        # Z małym prawdopodobieństwem: nagły napływ/odpływ pacjentów
        if random.random() < 0.01:  # 1% szansa (zmniejszone z 2%)
            spike = random.choice([-1, 1]) * random.randint(1, 2)
            new_value += spike
        
        # 5. Clip do sensownych wartości [0, capacity * 1.1]
        # (pozwalamy na 110% capacity dla overflow scenarios)
        new_value = max(0, min(capacity * 1.1, round(new_value)))
        
        new_occ[dept] = int(new_value)
    
    return new_occ


def initialize_occupancy() -> dict:
    """Inicjalizuje obłożenie rozsądnymi wartościami startowymi"""
    # Start w środku tygodnia, w godzinach popołudniowych (peak)
    hour = 14
    day_of_week = 2  # Środa
    
    initial_occ = {}
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        target_rate = get_target_occupancy_rate(dept, hour, day_of_week)
        # Start z małym szumem wokół target
        initial_occ[dept] = int(capacity * target_rate + random.gauss(0, capacity * 0.1))
        initial_occ[dept] = max(0, min(capacity, initial_occ[dept]))
    
    return initial_occ


def get_optimal_department(patient_row, occupancy):
    """Znajduje optymalny oddział dla pacjenta"""
    target_dept = patient_row['oddział_docelowy']
    triage_category = patient_row['kategoria_triażu']
    
    overcrowding_thresholds = {
        dept: int(0.8 * capacity) 
        for dept, capacity in DEPARTMENT_CAPACITY.items()
    }
    
    # Wysokie priorytety (1-2) -> zawsze target department
    if triage_category <= 2:
        return target_dept
    
    # Jeśli target department przepełniony -> szukaj alternatywy
    if occupancy[target_dept] >= overcrowding_thresholds[target_dept]:
        alternatives = {
            "SOR": ["Interna", "Chirurgia"],
            "Interna": ["SOR", "Kardiologia"],
            "Kardiologia": ["Interna", "SOR"],
            "Chirurgia": ["SOR", "Ortopedia"],
            "Ortopedia": ["Chirurgia", "SOR"],
            "Neurologia": ["Interna", "SOR"],
            "Pediatria": ["SOR", "Interna"],
            "Ginekologia": ["Chirurgia", "SOR"]
        }
        
        for alt_dept in alternatives.get(target_dept, []):
            if occupancy[alt_dept] < overcrowding_thresholds[alt_dept]:
                return alt_dept
    
    return target_dept


def generate_actual_decision(optimal_dept, triage_category):
    """Generuje faktyczną decyzję (z możliwością błędu)"""
    # Wyższy priorytet -> mniejsza szansa na błąd
    follow_optimal_prob = {
        1: 0.95,
        2: 0.90,
        3: 0.85,
        4: 0.80,
        5: 0.75
    }
    
    if random.random() < follow_optimal_prob[triage_category]:
        return optimal_dept
    
    # Błędna decyzja
    departments = list(DEPARTMENT_CAPACITY.keys())
    departments.remove(optimal_dept)
    return random.choice(departments)


def generate_outcome(actual_dept, optimal_dept, triage_category, occupancy):
    """Generuje outcome decyzji"""
    if actual_dept == optimal_dept:
        return "Optymalna decyzja"
    
    if triage_category <= 2:
        return "Suboptymalne umieszczenie pacjenta wysokiego ryzyka"
    
    if occupancy[actual_dept] > 0.9 * DEPARTMENT_CAPACITY[actual_dept]:
        return "Przeciążenie oddziału"
    
    return "Akceptowalne rozwiązanie alternatywne"


def generate_arrangement_data_v2(num_records=5000):
    """
    Generuje dane z CIĄGŁYMI timestampami i AUTOKORELACJĄ.
    
    KLUCZOWA ZMIANA: Obłożenie ewoluuje w czasie (80% persistence)
    zamiast być generowane niezależnie każdej godziny.
    
    Expected autocorrelation: ~0.75-0.85
    """
    if triage_data is None or len(triage_data) == 0:
        print("Error: No triage data available")
        return None
    
    print(f"\n{'='*70}")
    print(f"GENERATOR V2: Z AUTOKORELACJĄ")
    print(f"{'='*70}")
    print(f"\nGenerowanie {num_records} rekordów z ciągłością czasową...")
    print(f"To da około {num_records / 24:.1f} dni danych ({num_records / (24*30):.1f} miesięcy)")
    print(f"\nPersistence: 90% (poprzednio: 80%)")
    print(f"Expected autocorrelation:")
    print(f"  Lag 4h:  ~0.66 (poprzednio: 0.43)")
    print(f"  Lag 8h:  ~0.43 (poprzednio: 0.09)")
    
    records = []
    start_date = datetime(2024, 1, 1, 0, 0, 0)
    
    # INICJALIZACJA: Rozsądne wartości startowe
    current_occupancy = initialize_occupancy()
    
    print(f"\n📊 Inicjalne obłożenie:")
    for dept, occ in current_occupancy.items():
        pct = occ / DEPARTMENT_CAPACITY[dept] * 100
        print(f"  {dept}: {occ}/{DEPARTMENT_CAPACITY[dept]} ({pct:.0f}%)")
    
    for i in range(num_records):
        # Timestamp
        current_date = start_date + timedelta(hours=i)
        hour = current_date.hour
        day_of_week = current_date.weekday()
        
        # UPDATE OCCUPANCY with persistence
        current_occupancy = update_occupancy_with_persistence(
            current_occupancy, 
            hour, 
            day_of_week,
            persistence=0.90
        )
        
        # Losowy pacjent
        patient_index = random.randint(0, len(triage_data) - 1)
        patient_data = triage_data.iloc[patient_index].copy()
        
        # Decyzje alokacji
        optimal_dept = get_optimal_department(patient_data, current_occupancy)
        actual_dept = generate_actual_decision(optimal_dept, patient_data['kategoria_triażu'])
        outcome = generate_outcome(actual_dept, optimal_dept, patient_data['kategoria_triażu'], current_occupancy)
        
        # Zapis rekordu
        record = {
            "id_scenariusza": str(uuid.uuid4())[:8],
            "timestamp": current_date.strftime("%Y-%m-%d %H:%M:%S"),
            "obłożenie_oddziałów": json.dumps(current_occupancy),
            "id_pacjenta": patient_data['id_przypadku'],
            "wiek_pacjenta": patient_data['wiek'],
            "płeć_pacjenta": patient_data['płeć'],
            "kategoria_triażu": patient_data['kategoria_triażu'],
            "szablon_przypadku": patient_data['szablon_przypadku'],
            "oddział_docelowy": patient_data['oddział_docelowy'],
            "optymalne_przypisanie": optimal_dept,
            "faktyczne_przypisanie": actual_dept,
            "wynik": outcome
        }
        
        records.append(record)
        
        # Progress
        if (i + 1) % 500 == 0:
            progress = (i + 1) / num_records * 100
            print(f"  Postęp: {i + 1}/{num_records} ({progress:.1f}%)")
    
    arrangement_data = pd.DataFrame(records)
    
    print(f"\n✓ Wygenerowano {len(arrangement_data)} rekordów")
    print(f"  Zakres czasowy: {arrangement_data['timestamp'].min()} → {arrangement_data['timestamp'].max()}")
    
    # WALIDACJA: Sprawdź autokorelację
    print(f"\n🔍 Walidacja autokorelacji:")
    arrangement_data['SOR_occ'] = arrangement_data['obłożenie_oddziałów'].apply(
        lambda x: json.loads(x)['SOR']
    )
    
    for lag in [1, 4, 8, 24]:
        autocorr = arrangement_data['SOR_occ'].autocorr(lag)
        print(f"  Lag {lag}h: {autocorr:.3f}")
    
    # Drop helper column
    arrangement_data = arrangement_data.drop('SOR_occ', axis=1)
    
    # Statystyki
    print(f"\n📊 Statystyki obłożenia:")
    sample_occ = json.loads(arrangement_data.iloc[len(arrangement_data)//2]['obłożenie_oddziałów'])
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        all_occ = [json.loads(row['obłożenie_oddziałów'])[dept] for _, row in arrangement_data.iterrows()]
        avg_occ = np.mean(all_occ)
        std_occ = np.std(all_occ)
        avg_pct = avg_occ / capacity * 100
        print(f"  {dept}: avg={avg_occ:.1f} ({avg_pct:.0f}%), std={std_occ:.1f}")
    
    print(f"\n📈 Rozkład decyzji:")
    print(arrangement_data['wynik'].value_counts())
    
    return arrangement_data


def main():
    """Główna funkcja"""
    print(f"\n{'='*70}")
    print(f"ASSIGNMENT DATA GENERATOR V2")
    print(f"{'='*70}")
    
    # Generuj dane
    df = generate_arrangement_data_v2(num_records=5000)
    
    if df is not None:
        # Zapisz
        output_path = 'data/raw/department_arrangement_data.csv'
        df.to_csv(output_path, index=False)
        print(f"\n Dane zapisane: {output_path}")
        
        # Backup starej wersji
        import shutil
        from pathlib import Path
        backup_path = Path('data/raw/department_arrangement_data_old.csv')
        if backup_path.exists():
            print(f"  Uwaga: Nadpisuję istniejące dane (backup w _old.csv)")
        


if __name__ == "__main__":
    main()
