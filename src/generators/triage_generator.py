import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
from config.constants import MEDICAL_CASE_TEMPLATES

def generate_case(template_name, template):
    """Generuje jeden przypadek medyczny"""
    case = {
        'id_przypadku': str(uuid.uuid4())[:8],
        'szablon_przypadku': template_name,
        'data_przyjęcia': datetime.now() - timedelta(days=np.random.randint(0, 365))
    }
    
    case['wiek'] = np.random.randint(*template['demografia']['wiek'])
    case['płeć'] = 'M' if np.random.random() < template['demografia']['płeć_M'] else 'K'
    
    for param, (min_val, max_val) in template['parametry'].items():
        case[param] = round(np.random.uniform(min_val, max_val), 1)
    
    probs = template['prawdopodobieństwa_triażu']
    case['kategoria_triażu'] = np.random.choice([1,2,3,4,5], p=probs)
    
    case['oddział_docelowy'] = np.random.choice(template['oddział_docelowy'])
    
    return case

if __name__ == '__main__':
    print("="*70)
    print("GENEROWANIE DANYCH Z REALISTYCZNYM SZUMEM")
    print("="*70)
    
    templates_by_dominant = {1: [], 2: [], 3: [], 4: [], 5: []}
    
    for name, template in MEDICAL_CASE_TEMPLATES.items():
        probs = template['prawdopodobieństwa_triażu']
        dominant_cat = probs.index(max(probs)) + 1  
        templates_by_dominant[dominant_cat].append((name, template))
    
    print("\nSzablony według dominującej kategorii:")
    for cat, templates in templates_by_dominant.items():
        print(f"  Kategoria {cat}: {len(templates)} szablonów")
        for name, _ in templates:
            print(f"    - {name}")
    
    cases = []
    target_per_category = 4000
    
    for cat in range(1, 6):
        templates = templates_by_dominant[cat]
        if not templates:
            print(f"\n Brak szablonów dla kategorii {cat}")
            continue
            
        for i in range(target_per_category):
            name, template = templates[i % len(templates)]
            cases.append(generate_case(name, template))
    
    df = pd.DataFrame(cases)
    output = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'triage_data.csv'
    df.to_csv(output, index=False)
    
    for cat in range(1, 6):
        count = (df['kategoria_triażu'] == cat).sum()
        pct = count / len(df) * 100
        print(f"  Kategoria {cat}: {count:>4} ({pct:>5.1f}%)")
    
    print(f"{'='*70}")
