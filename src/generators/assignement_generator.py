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

def generate_department_occupancy():
    occupancy = {}
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        occupancy[dept] = int(capacity * random.uniform(0.3, 0.95))
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
    #czym wieksza kategoria triażu tym mniejsza szansa na pomyłke
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

def generate_arrangement_data(num_records=300):
    if triage_data is None or len(triage_data) == 0:
        print("Error: No triage data available")
        return None
        
    records = []
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    for _ in range(num_records):
        current_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        occupancy = generate_department_occupancy()
        
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
    arrangement_data = pd.DataFrame(records)
    
    arrangement_data = arrangement_data.sort_values('timestamp')
    
    return arrangement_data

if __name__ == "__main__":
    arrangement_data = generate_arrangement_data(300)
    
    if arrangement_data is not None:
        output_path = 'data/raw/department_arrangement_data.csv'
        try:
            arrangement_data.to_csv(output_path, index=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    else:
        print("Failed to generate arrangement data")
