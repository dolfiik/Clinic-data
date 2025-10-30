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
    """Docelowy wskaźnik obłożenia (0-1) based on time patterns"""
    is_weekend = day_of_week >= 5
    is_night = hour < 6 or hour >= 22
    is_peak_hours = 8 <= hour <= 20
    
    if dept == "SOR":
        base_rate = 0.65
        if 18 <= hour <= 23:
            base_rate = 0.85
        elif 0 <= hour < 6:
            base_rate = 0.55
        elif 6 <= hour < 10:
            base_rate = 0.60
    else:
        base_rate = 0.50
        if is_peak_hours:
            base_rate = 0.65
        if is_night:
            base_rate = 0.35
    
    if is_weekend:
        if dept in ["Chirurgia", "Ortopedia", "Ginekologia"]:
            base_rate *= 0.60
        elif dept != "SOR":
            base_rate *= 0.80
    
    if day_of_week == 0 and dept != "SOR":
        base_rate = min(0.90, base_rate + 0.15)
    
    if day_of_week == 4 and hour >= 14:
        base_rate *= 0.85
    
    return max(0.2, min(0.95, base_rate))


def update_occupancy_with_persistence(
    current_occ: dict,
    hour: int,
    day_of_week: int,
    persistence: float = 0.90
) -> dict:
    """Aktualizuje obłożenie z CIĄGŁOŚCIĄ"""
    new_occ = {}
    
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        prev_value = current_occ[dept]
        target_rate = get_target_occupancy_rate(dept, hour, day_of_week)
        target_value = capacity * target_rate
        noise_std = capacity * 0.02
        
        new_value = (
            persistence * prev_value +
            (1 - persistence) * 0.80 * target_value +
            np.random.normal(0, noise_std)
        )
        
        if random.random() < 0.01:
            spike = random.choice([-1, 1]) * random.randint(1, 2)
            new_value += spike
        
        new_value = max(0, min(capacity * 1.1, round(new_value)))
        new_occ[dept] = int(new_value)
    
    return new_occ


def initialize_occupancy() -> dict:
    """Inicjalizuje obłożenie rozsądnymi wartościami"""
    hour = 14
    day_of_week = 2
    
    initial_occ = {}
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        target_rate = get_target_occupancy_rate(dept, hour, day_of_week)
        initial_occ[dept] = int(capacity * target_rate + random.gauss(0, capacity * 0.1))
        initial_occ[dept] = max(0, min(capacity, initial_occ[dept]))
    
    return initial_occ


def calculate_department_score(
    dept: str,
    occupancy: dict,
    patient_triage: int,
    is_medically_compatible: bool
) -> float:
    """
    Oblicza score dla danego oddziału (wyższy = lepszy)
    
    Factors:
    - Medical compatibility (ważne!)
    - Current occupancy (wolne łóżka preferowane)
    - Triage priority (wysokie priority → preferuj target)
    """
    capacity = DEPARTMENT_CAPACITY[dept]
    current_occ = occupancy[dept]
    occupancy_rate = current_occ / capacity
    
    score = 100.0
    
    # 1. Medical compatibility (najważniejsze!)
    if not is_medically_compatible:
        score -= 80  # Bardzo duża kara
    
    # 2. Occupancy penalty (liniowy)
    # 0% occ → 0 penalty
    # 100% occ → -50 penalty
    occupancy_penalty = occupancy_rate * 50
    score -= occupancy_penalty
    
    # 3. Overcrowding penalty (jeśli >75% - zmniejszone z 80%)
    if occupancy_rate > 0.75:
        overcrowding_penalty = (occupancy_rate - 0.75) * 150  # Zwiększone z 100
        score -= overcrowding_penalty
    
    # 4. Critical overcrowding (>90% - zmniejszone z 95%)
    if occupancy_rate > 0.90:
        score -= 70  # Zwiększone z 50
    
    # 5. Bonus dla wysokiego priorytetu w target dept
    # (to jest obsługiwane przez is_medically_compatible już)
    
    return score


def get_medical_compatibility(szablon: str, dept: str) -> bool:
    """Sprawdza czy pacjent jest medically compatible z oddziałem"""
    szablon_to_depts = {
        'ból w klatce piersiowej': ['Kardiologia', 'SOR', 'Interna'],
        'zaostrzenie astmy': ['Interna', 'SOR'],
        'uraz głowy': ['Neurologia', 'SOR', 'Chirurgia'],
        'złamanie kończyny': ['Ortopedia', 'SOR', 'Chirurgia'],
        'udar': ['Neurologia', 'SOR'],
        'zaburzenia rytmu serca': ['Kardiologia', 'SOR', 'Interna'],
        'zapalenie płuc': ['Interna', 'SOR'],
        'zapalenie wyrostka': ['Chirurgia', 'SOR'],
        'silne krwawienie': ['Chirurgia', 'SOR'],
        'krwawienie z przewodu pokarmowego': ['Chirurgia', 'Interna', 'SOR'],
        'napad padaczkowy': ['Neurologia', 'SOR'],
        'omdlenie': ['Kardiologia', 'Neurologia', 'SOR', 'Interna'],
        'ból brzucha': ['Chirurgia', 'Interna', 'Ginekologia', 'SOR'],
        'reakcja alergiczna': ['Interna', 'SOR'],
        'migrena': ['Neurologia', 'SOR'],
        'zatrucie pokarmowe': ['Interna', 'SOR'],
        'infekcja układu moczowego': ['Interna', 'SOR', 'Ginekologia'],
        'zapalenie opon mózgowych': ['Neurologia', 'SOR'],
        'zaostrzenie POChP': ['Interna', 'SOR'],
        'uraz wielonarządowy': ['Chirurgia', 'SOR']
    }
    
    compatible_depts = szablon_to_depts.get(szablon, ['SOR'])
    return dept in compatible_depts


def get_optimal_department_v3(patient_row, occupancy) -> str:
    """
    NOWA WERSJA: Faktyczna optymalizacja z scoring system
    
    Returns:
        Nazwa optymalnego oddziału
    """
    target_dept = patient_row['oddział_docelowy']
    triage_category = patient_row['kategoria_triażu']
    szablon = patient_row['szablon_przypadku']
    
    # HIGH PRIORITY (1-2): ZAWSZE target department (bezpieczeństwo!)
    if triage_category <= 2:
        return target_dept
    
    # MEDIUM/LOW PRIORITY (3-5): Optymalizuj based on occupancy
    
    # Oblicz score dla wszystkich compatibilnych oddziałów
    scores = {}
    
    for dept in DEPARTMENT_CAPACITY.keys():
        is_compatible = get_medical_compatibility(szablon, dept)
        
        # Target dept dostaje bonus
        is_target = (dept == target_dept)
        
        score = calculate_department_score(
            dept, occupancy, triage_category, is_compatible
        )
        
        # Target bonus (preferujemy target jeśli możliwe)
        if is_target:
            score += 10  # Zmniejszone z 20 → 10
        
        scores[dept] = score
    
    best_dept = max(scores, key=scores.get)
    best_score = scores[best_dept]
    
    if scores[target_dept] > -40 and random.random() < 0.35:
        return target_dept
    
    if best_score > scores[target_dept] + 12:
        return best_dept
    
    # W pozostałych przypadkach, zostań w target
    return target_dept


def generate_actual_decision(optimal_dept, triage_category):
    """Generuje faktyczną decyzję (z możliwością błędu)"""
    follow_optimal_prob = {
        1: 0.98,
        2: 0.95,
        3: 0.90,
        4: 0.85,
        5: 0.80
    }
    
    if random.random() < follow_optimal_prob[triage_category]:
        return optimal_dept
    
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


def generate_arrangement_data_v3(num_records=5000):
    """Generuje dane z PRAWDZIWĄ optymalizacją"""
    if triage_data is None or len(triage_data) == 0:
        print("Error: No triage data available")
        return None
    
    print(f"\n{'='*70}")
    print(f"GENERATOR V3: Z PRAWDZIWĄ OPTYMALIZACJĄ")
    print(f"{'='*70}")
    print(f"\nGenerowanie {num_records} rekordów...")
    print(f"Expected: ~20-30% przypadków z realokacją")
    
    records = []
    start_date = datetime(2024, 1, 1, 0, 0, 0)
    
    current_occupancy = initialize_occupancy()
    
    print(f"\n📊 Inicjalne obłożenie:")
    for dept, occ in current_occupancy.items():
        pct = occ / DEPARTMENT_CAPACITY[dept] * 100
        print(f"  {dept}: {occ}/{DEPARTMENT_CAPACITY[dept]} ({pct:.0f}%)")
    
    reallocation_count = 0
    
    for i in range(num_records):
        current_date = start_date + timedelta(hours=i)
        hour = current_date.hour
        day_of_week = current_date.weekday()
        
        # Update occupancy
        current_occupancy = update_occupancy_with_persistence(
            current_occupancy, hour, day_of_week, persistence=0.90
        )
        
        # Losowy pacjent
        patient_index = random.randint(0, len(triage_data) - 1)
        patient_data = triage_data.iloc[patient_index].copy()
        
        # OPTYMALNA alokacja (v3 - z faktyczną optymalizacją!)
        optimal_dept = get_optimal_department_v3(patient_data, current_occupancy)
        
        # Faktyczna decyzja
        actual_dept = generate_actual_decision(optimal_dept, patient_data['kategoria_triażu'])
        
        # Outcome
        outcome = generate_outcome(actual_dept, optimal_dept, patient_data['kategoria_triażu'], current_occupancy)
        
        # Track reallocations
        if optimal_dept != patient_data['oddział_docelowy']:
            reallocation_count += 1
        
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
        
        if (i + 1) % 500 == 0:
            progress = (i + 1) / num_records * 100
            realloc_pct = reallocation_count / (i + 1) * 100
            print(f"  Postęp: {i + 1}/{num_records} ({progress:.1f}%) | Realokacji: {realloc_pct:.1f}%")
    
    arrangement_data = pd.DataFrame(records)
    
    print(f"\n✓ Wygenerowano {len(arrangement_data)} rekordów")
    
    # WALIDACJA
    print(f"\n🔍 Walidacja optymalizacji:")
    
    different = (arrangement_data['optymalne_przypisanie'] != arrangement_data['oddział_docelowy']).sum()
    different_pct = different / len(arrangement_data) * 100
    
    print(f"  Przypadki z realokacją: {different} ({different_pct:.1f}%)")
    print(f"  ✅ Expected: 20-30%, Got: {different_pct:.1f}%")
    
    if different_pct < 10:
        print(f"  ⚠️  WARNING: Za mało realokacji! Sprawdź thresholds.")
    elif different_pct > 40:
        print(f"  ⚠️  WARNING: Za dużo realokacji! Model może być niestabilny.")
    else:
        print(f"  ✅ Realokacje w dobrym zakresie!")
    
    print(f"\n📊 Rozkład optymalnych przypisań:")
    print(arrangement_data['optymalne_przypisanie'].value_counts())
    
    print(f"\n📈 Rozkład decyzji:")
    print(arrangement_data['wynik'].value_counts())
    
    return arrangement_data


def main():
    """Główna funkcja"""
    print(f"\n{'='*70}")
    print(f"ASSIGNMENT DATA GENERATOR V3")
    print(f"{'='*70}")
    
    df = generate_arrangement_data_v3(num_records=5000)
    
    if df is not None:
        output_path = 'data/raw/department_arrangement_data.csv'
        df.to_csv(output_path, index=False)
        print(f"\n Dane zapisane: {output_path}")
        

if __name__ == "__main__":
    main()
