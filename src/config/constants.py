DEPARTMENTS = [
    "SOR", "Interna", "Kardiologia", "Chirurgia",
    "Ortopedia", "Neurologia", "Pediatria", "Ginekologia"
]

DEPARTMENT_CAPACITY = {
    "SOR": 25, "Interna": 50, "Kardiologia": 30, "Chirurgia": 35,
    "Ortopedia": 25, "Neurologia": 20, "Pediatria": 30, "Ginekologia": 20
}

MEDICAL_CASE_TEMPLATES = {
    
    "zawał_STEMI": {
        "demografia": {"wiek": (45, 85), "płeć_M": 0.7},
        "parametry": {
            "tętno": (80, 160),           
            "ciśnienie_skurczowe": (70, 140),  
            "ciśnienie_rozkurczowe": (40, 80),
            "temperatura": (36.0, 38.0),
            "saturacja": (80, 96),         
            "GCS": (8, 15),              
            "ból": (7, 10),
            "częstotliwość_oddechów": (18, 40),
            "czas_od_objawów_h": (0.5, 6)
        },
        "prawdopodobieństwa_triażu": [0.85, 0.12, 0.03, 0.0, 0.0],  
        "oddział_docelowy": ["Kardiologia", "SOR"]
    },
    
    "udar_ciężki": {
        "demografia": {"wiek": (55, 90), "płeć_M": 0.55},
        "parametry": {
            "tętno": (50, 130),
            "ciśnienie_skurczowe": (140, 240),
            "ciśnienie_rozkurczowe": (80, 140),
            "temperatura": (36.0, 38.5),
            "saturacja": (85, 98),         
            "GCS": (5, 14),               
            "ból": (0, 7),
            "częstotliwość_oddechów": (8, 32),
            "czas_od_objawów_h": (0.5, 6)
        },
        "prawdopodobieństwa_triażu": [0.80, 0.15, 0.05, 0.0, 0.0],
        "oddział_docelowy": ["Neurologia", "SOR"]
    },
    
    "uraz_wielonarządowy": {
        "demografia": {"wiek": (15, 65), "płeć_M": 0.75},
        "parametry": {
            "tętno": (100, 160),
            "ciśnienie_skurczowe": (60, 110),
            "ciśnienie_rozkurczowe": (30, 70),
            "temperatura": (34.0, 37.0),
            "saturacja": (70, 92),
            "GCS": (3, 12),
            "ból": (7, 10),
            "częstotliwość_oddechów": (20, 45),
            "czas_od_objawów_h": (0.25, 3)
        },
        "prawdopodobieństwa_triażu": [0.90, 0.08, 0.02, 0.0, 0.0],
        "oddział_docelowy": ["SOR", "Chirurgia"]
    },
    
    "zapalenie_płuc_ciężkie": {
        "demografia": {"wiek": (30, 85), "płeć_M": 0.5},
        "parametry": {
            "tętno": (85, 130),           
            "ciśnienie_skurczowe": (95, 150),
            "ciśnienie_rozkurczowe": (55, 95),
            "temperatura": (37.5, 40.5),
            "saturacja": (84, 95),       
            "GCS": (13, 15),
            "ból": (4, 8),
            "częstotliwość_oddechów": (22, 35),
            "czas_od_objawów_h": (8, 72)
        },
        "prawdopodobieństwa_triażu": [0.08, 0.80, 0.10, 0.02, 0.0],  
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "zapalenie_wyrostka": {
        "demografia": {"wiek": (8, 55), "płeć_M": 0.5},
        "parametry": {
            "tętno": (75, 120),
            "ciśnienie_skurczowe": (100, 145),
            "ciśnienie_rozkurczowe": (65, 95),
            "temperatura": (37.0, 39.5),
            "saturacja": (94, 100),
            "GCS": (14, 15),
            "ból": (5, 9),
            "częstotliwość_oddechów": (14, 26),
            "czas_od_objawów_h": (4, 48)
        },
        "prawdopodobieństwa_triażu": [0.05, 0.85, 0.08, 0.02, 0.0],
        "oddział_docelowy": ["Chirurgia", "SOR"]
    },
    
    "silne_krwawienie": {
        "demografia": {"wiek": (18, 75), "płeć_M": 0.6},
        "parametry": {
            "tętno": (85, 130),
            "ciśnienie_skurczowe": (85, 130),
            "ciśnienie_rozkurczowe": (55, 85),
            "temperatura": (36.0, 37.5),
            "saturacja": (90, 98),
            "GCS": (13, 15),
            "ból": (5, 9),
            "częstotliwość_oddechów": (16, 28),
            "czas_od_objawów_h": (0.5, 12)
        },
        "prawdopodobieństwa_triażu": [0.10, 0.82, 0.08, 0.0, 0.0],
        "oddział_docelowy": ["Chirurgia", "SOR"]
    },
    
    "złamanie_proste": {
        "demografia": {"wiek": (8, 75), "płeć_M": 0.6},
        "parametry": {
            "tętno": (65, 105),            
            "ciśnienie_skurczowe": (100, 145),
            "ciśnienie_rozkurczowe": (65, 95),
            "temperatura": (36.3, 37.8),
            "saturacja": (95, 100),
            "GCS": (15, 15),
            "ból": (4, 8),
            "częstotliwość_oddechów": (12, 22),
            "czas_od_objawów_h": (0.5, 48)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.10, 0.80, 0.10, 0.0],  
        "oddział_docelowy": ["Ortopedia", "SOR"]
    },
    
    "infekcja_moczu": {
        "demografia": {"wiek": (18, 85), "płeć_M": 0.25},
        "parametry": {
            "tętno": (70, 100),
            "ciśnienie_skurczowe": (105, 145),
            "ciśnienie_rozkurczowe": (65, 95),
            "temperatura": (37.0, 39.0),
            "saturacja": (95, 100),
            "GCS": (15, 15),
            "ból": (3, 7),
            "częstotliwość_oddechów": (12, 20),
            "czas_od_objawów_h": (12, 96)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.05, 0.85, 0.10, 0.0],
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "zaostrzenie_astmy": {
        "demografia": {"wiek": (12, 65), "płeć_M": 0.45},
        "parametry": {
            "tętno": (75, 115),
            "ciśnienie_skurczowe": (105, 140),
            "ciśnienie_rozkurczowe": (65, 90),
            "temperatura": (36.5, 37.8),
            "saturacja": (88, 96),        
            "GCS": (15, 15),
            "ból": (2, 6),
            "częstotliwość_oddechów": (18, 32),
            "czas_od_objawów_h": (1, 24)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.15, 0.75, 0.10, 0.0],  
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "ból_brzucha_łagodny": {
        "demografia": {"wiek": (12, 70), "płeć_M": 0.45},
        "parametry": {
            "tętno": (60, 95),             
            "ciśnienie_skurczowe": (105, 140),
            "ciśnienie_rozkurczowe": (65, 90),
            "temperatura": (36.5, 38.0),
            "saturacja": (96, 100),
            "GCS": (15, 15),
            "ból": (2, 6),
            "częstotliwość_oddechów": (12, 20),
            "czas_od_objawów_h": (4, 72)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.15, 0.80, 0.05],  
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "skręcenie_lekkie": {
        "demografia": {"wiek": (12, 55), "płeć_M": 0.55},
        "parametry": {
            "tętno": (60, 90),
            "ciśnienie_skurczowe": (105, 135),
            "ciśnienie_rozkurczowe": (65, 88),
            "temperatura": (36.4, 37.2),
            "saturacja": (97, 100),
            "GCS": (15, 15),
            "ból": (2, 7),
            "częstotliwość_oddechów": (12, 18),
            "czas_od_objawów_h": (1, 72)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.12, 0.83, 0.05],
        "oddział_docelowy": ["Ortopedia", "SOR"]
    },
    
    "migrena": {
        "demografia": {"wiek": (16, 60), "płeć_M": 0.3},
        "parametry": {
            "tętno": (65, 95),
            "ciśnienie_skurczowe": (100, 140),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.4, 37.3),
            "saturacja": (97, 100),
            "GCS": (15, 15),
            "ból": (5, 9),                 
            "częstotliwość_oddechów": (12, 18),
            "czas_od_objawów_h": (2, 48)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.10, 0.85, 0.05],
        "oddział_docelowy": ["Neurologia", "SOR"]
    },
    
    "przeziębienie": {
        "demografia": {"wiek": (3, 65), "płeć_M": 0.5},
        "parametry": {
            "tętno": (60, 85),
            "ciśnienie_skurczowe": (105, 130),
            "ciśnienie_rozkurczowe": (65, 85),
            "temperatura": (36.5, 38.3),   
            "saturacja": (96, 100),
            "GCS": (15, 15),
            "ból": (1, 4),
            "częstotliwość_oddechów": (12, 18),
            "czas_od_objawów_h": (24, 168)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.0, 0.15, 0.85],  
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "kontrola": {
        "demografia": {"wiek": (18, 80), "płeć_M": 0.5},
        "parametry": {
            "tętno": (58, 80),
            "ciśnienie_skurczowe": (105, 135),
            "ciśnienie_rozkurczowe": (65, 88),
            "temperatura": (36.3, 37.2),
            "saturacja": (97, 100),
            "GCS": (15, 15),
            "ból": (0, 2),
            "częstotliwość_oddechów": (12, 16),
            "czas_od_objawów_h": (168, 720)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.0, 0.10, 0.90],
        "oddział_docelowy": ["Interna"]
    },
    
    "receptura": {
        "demografia": {"wiek": (25, 85), "płeć_M": 0.5},
        "parametry": {
            "tętno": (58, 78),
            "ciśnienie_skurczowe": (108, 132),
            "ciśnienie_rozkurczowe": (68, 86),
            "temperatura": (36.4, 37.1),
            "saturacja": (97, 100),
            "GCS": (15, 15),
            "ból": (0, 2),
            "częstotliwość_oddechów": (12, 16),
            "czas_od_objawów_h": (72, 360)
        },
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.0, 0.08, 0.92],
        "oddział_docelowy": ["Interna", "SOR"]
    }
}

TRIAGE_SERVICE_TIMES = {1: 15, 2: 30, 3: 60, 4: 90, 5: 120}
TRIAGE_WAIT_TIMES = {1: 0, 2: 10, 3: 30, 4: 60, 5: 120}
