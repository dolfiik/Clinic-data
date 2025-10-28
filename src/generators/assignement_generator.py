import pandas as pd
import random
from datetime import datetime, timedelta
import uuid
import json

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

def generate_department_occupancy(hour=12, day_of_week=0):
    """
    Generuje obłożenie oddziałów z uwzględnieniem sezonowości.
    
    Args:
        hour: Godzina dnia (0-23)
        day_of_week: Dzień tygodnia (0=Poniedziałek, 6=Niedziela)
    """
    occupancy = {}
    is_weekend = day_of_week >= 5
    is_night = hour < 6 or hour >= 22
    is_peak_hours = 8 <= hour <= 20
    
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        # Bazowy wskaźnik obłożenia
        base_rate = random.uniform(0.3, 0.7)
        
        # SOR - zawsze bardziej obciążony, szczególnie wieczorami
        if dept == "SOR":
            base_rate = random.uniform(0.5, 0.85)
            if 18 <= hour <= 23:  # Wieczorny szczyt
                base_rate = min(0.95, base_rate + 0.15)
        
        # Godziny szczytu (8-20) - więcej pacjentów
        if is_peak_hours and dept != "SOR":
            base_rate = min(0.90, base_rate + 0.20)
        
        # Noc (22-6) - mniej pacjentów (poza SOR)
        if is_night and dept != "SOR":
            base_rate *= 0.6
        
        # Weekend - mniej pacjentów na oddziałach planowych
        if is_weekend:
            if dept in ["Chirurgia", "Ortopedia", "Ginekologia"]:
                base_rate *= 0.70  # Dużo mniej planowych zabiegów
            elif dept != "SOR":
                base_rate *= 0.85
        
        # Poniedziałek - więcej pacjentów po weekendzie
        if day_of_week == 0 and dept != "SOR":
            base_rate = min(0.95, base_rate + 0.10)
        
        # Dodaj lekki szum dla realizmu
        noise = random.uniform(-0.05, 0.05)
        base_rate = max(0.1, min(0.98, base_rate + noise))
        
        occupancy[dept] = int(capacity * base_rate)
    
    return occupancy

def get_optimal_department(patient_row, occupancy):
    target_dept = patient_row['oddział_docelowy']
    triage_category = patient_row['kategoria_triażu']
    
    overcrowding_thresholds = {dept: int(0.8 * capacity) for dept, capacity in DEPARTMENT_CAPACITY.items()}
    
    if occupancy[target_dept] >= overcrowding_thresholds[target_dept]:
        if triage_category <= 2:
            return target_dept
        
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
        
        for alt_dept in alternatives[target_dept]:
            if occupancy[alt_dept] < overcrowding_thresholds[alt_dept]:
                return alt_dept
    
    return target_dept

def generate_actual_decision(optimal_dept, triage_category):
    # Czym większa kategoria triażu tym mniejsza szansa na pomyłkę
    follow_optimal_prob = {
        1: 0.95,  
        2: 0.90,
        3: 0.85,
        4: 0.80,
        5: 0.75  
    }
    
    if random.random() < follow_optimal_prob[triage_category]:
        return optimal_dept
    
    departments = list(DEPARTMENT_CAPACITY.keys())
    departments.remove(optimal_dept)
    return random.choice(departments)

def generate_outcome(actual_dept, optimal_dept, triage_category, occupancy):
    if actual_dept == optimal_dept:
        return "Optymalna decyzja"
    
    if triage_category <= 2:
        return "Suboptymalne umieszczenie pacjenta wysokiego ryzyka"
    
    if occupancy[actual_dept] > 0.9 * DEPARTMENT_CAPACITY[actual_dept]:
        return "Przeciążenie oddziału"
    
    return "Akceptowalne rozwiązanie alternatywne"

def generate_arrangement_data(num_records=5000):
    """
    Generuje dane z CIĄGŁYMI timestampami (co godzinę) dla modelu LSTM.
    
    Args:
        num_records: Liczba rekordów (domyślnie 5000 = ~7 miesięcy danych)
    """
    if triage_data is None or len(triage_data) == 0:
        print("Error: No triage data available")
        return None
    
    print(f"Generowanie {num_records} rekordów z ciągłymi timestampami...")
    print(f"To da około {num_records / 24:.1f} dni danych ({num_records / (24*30):.1f} miesięcy)")
        
    records = []
    start_date = datetime(2024, 1, 1, 0, 0, 0)  # Początek o północy
    
    for i in range(num_records):
        # CIĄGŁE timestampy - co godzinę
        current_date = start_date + timedelta(hours=i)
        
        hour = current_date.hour
        day_of_week = current_date.weekday()
        
        # Generuj obłożenie z sezonowością
        occupancy = generate_department_occupancy(hour=hour, day_of_week=day_of_week)
        
        # Losowy pacjent z danych triażowych
        patient_index = random.randint(0, len(triage_data) - 1)
        patient_data = triage_data.iloc[patient_index].copy()
        
        optimal_dept = get_optimal_department(patient_data, occupancy)
        actual_dept = generate_actual_decision(optimal_dept, patient_data['kategoria_triażu'])
        outcome = generate_outcome(actual_dept, optimal_dept, patient_data['kategoria_triażu'], occupancy)
        
        record = {
            "id_scenariusza": str(uuid.uuid4())[:8],
            "timestamp": current_date.strftime("%Y-%m-%d %H:%M:%S"),
            "obłożenie_oddziałów": json.dumps(occupancy),
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
        
        # Progress bar co 500 rekordów
        if (i + 1) % 500 == 0:
            progress = (i + 1) / num_records * 100
            print(f"  Postęp: {i + 1}/{num_records} ({progress:.1f}%)")
    
    arrangement_data = pd.DataFrame(records)
    
    # Dane są już posortowane chronologicznie (bo generujemy sekwencyjnie)
    
    print(f"\n✓ Wygenerowano {len(arrangement_data)} rekordów")
    print(f"  Zakres czasowy: {arrangement_data['timestamp'].min()} → {arrangement_data['timestamp'].max()}")
    
    # Statystyki obłożenia
    print(f"\nStatystyki obłożenia oddziałów:")
    first_occupancy = json.loads(arrangement_data['obłożenie_oddziałów'].iloc[0])
    for dept in first_occupancy.keys():
        occupancies = [json.loads(row)[dept] for row in arrangement_data['obłożenie_oddziałów']]
        avg_occ = sum(occupancies) / len(occupancies)
        capacity = DEPARTMENT_CAPACITY[dept]
        print(f"  {dept}: średnio {avg_occ:.1f}/{capacity} ({avg_occ/capacity*100:.1f}%)")
    
    return arrangement_data

if __name__ == "__main__":
    print("="*70)
    print("GENERATOR DANYCH DO PROGNOZOWANIA OBCIĄŻENIA ODDZIAŁÓW")
    print("="*70)
    
    # Wygeneruj 5000 rekordów (około 7 miesięcy danych co godzinę)
    # Możesz zmienić na więcej: 8000 = 11 miesięcy, 10000 = 13 miesięcy
    arrangement_data = generate_arrangement_data(num_records=5000)
    
    if arrangement_data is not None:
        output_path = 'data/raw/department_arrangement_data.csv'
        try:
            arrangement_data.to_csv(output_path, index=False)
            print(f"\n✓ Dane zapisane: {output_path}")
            print(f"  Rozmiar pliku: {len(arrangement_data)} wierszy")
        except Exception as e:
            print(f"\n Error saving data: {e}")
    else:
        print("\n Failed to generate arrangement data")
    
    print("\n" + "="*70)
    print("GOTOWE! Możesz teraz trenować model LSTM.")
    print("="*70)
