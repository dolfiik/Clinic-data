"""
ULEPSZONE SZABLONY PRZYPADKÓW MEDYCZNYCH
Dodane cechy:
- GCS (Glasgow Coma Scale) 
- Poziom bólu (0-10)
- Częstotliwość oddechów
- Czas od początku objawów
- WYRAŹNIEJSZE różnice między kategoriami triażu
"""

DEPARTMENTS = [
    "SOR",
    "Interna",
    "Kardiologia",
    "Chirurgia",
    "Ortopedia",
    "Neurologia",
    "Pediatria",
    "Ginekologia"
]

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

# Szablony z dodatkowymi parametrami i WYRAŹNIEJSZYMI różnicami
MEDICAL_CASE_TEMPLATES = {
    
    "zawał_serca": {
        "demografia": {"wiek": (45, 85), "płeć_M": 0.65},
        "parametry": {
            "tętno": (50, 140),
            "ciśnienie_skurczowe": (80, 180),
            "ciśnienie_rozkurczowe": (40, 110),
            "temperatura": (36.0, 38.0),
            "saturacja": (85, 98),
            "GCS": (13, 15),  # NOWE
            "ból": (7, 10),   # NOWE - silny ból!
            "częstotliwość_oddechów": (16, 28),  # NOWE
            "czas_od_objawów_h": (0.5, 6)  # NOWE - czas krytyczny
        },
        "objawy": ["ból w klatce piersiowej", "duszność", "wymioty", "bladość", "pocenie się"],
        # KLUCZOWE: Wyraźne różnice w prawdopodobieństwach
        "prawdopodobieństwa_triażu": [0.85, 0.15, 0.0, 0.0, 0.0],  # 85% kat 1!
        "choroby_współistniejące": {
            "nadciśnienie": 0.7,
            "cukrzyca": 0.4,
            "otyłość": 0.5
        },
        "typ": "kardiologiczny",
        "oddział_docelowy": ["Kardiologia", "SOR"]
    },
    
    "udar_mózgu": {
        "demografia": {"wiek": (50, 90), "płeć_M": 0.55},
        "parametry": {
            "tętno": (60, 120),
            "ciśnienie_skurczowe": (140, 220),
            "ciśnienie_rozkurczowe": (80, 130),
            "temperatura": (36.0, 38.0),
            "saturacja": (90, 100),
            "GCS": (8, 15),  # NOWE - może być obniżone!
            "ból": (0, 6),   # NOWE - nie zawsze boli
            "częstotliwość_oddechów": (12, 24),
            "czas_od_objawów_h": (0.5, 4.5)  # Golden hour!
        },
        "objawy": ["niedowład", "zaburzenia mowy", "zawroty głowy", "zaburzenia świadomości"],
        "prawdopodobieństwa_triażu": [0.80, 0.18, 0.02, 0.0, 0.0],  # 80% kat 1
        "choroby_współistniejące": {
            "nadciśnienie": 0.8,
            "migotanie przedsionków": 0.3,
            "cukrzyca": 0.4
        },
        "typ": "neurologiczny",
        "oddział_docelowy": ["Neurologia", "SOR"]
    },
    
    "zapalenie_wyrostka": {
        "demografia": {"wiek": (5, 50), "płeć_M": 0.5},
        "parametry": {
            "tętno": (80, 120),
            "ciśnienie_skurczowe": (100, 140),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (37.5, 39.5),
            "saturacja": (96, 100),
            "GCS": (14, 15),  # Przytomny
            "ból": (6, 9),    # Silny ból brzucha
            "częstotliwość_oddechów": (16, 24),
            "czas_od_objawów_h": (6, 48)
        },
        "objawy": ["ból brzucha", "nudności", "wymioty", "gorączka", "brak apetytu"],
        "prawdopodobieństwa_triażu": [0.05, 0.70, 0.25, 0.0, 0.0],  # 70% kat 2
        "choroby_współistniejące": {},
        "typ": "chirurgiczny",
        "oddział_docelowy": ["Chirurgia", "SOR"]
    },
    
    "zapalenie_płuc": {
        "demografia": {"wiek": (1, 90), "płeć_M": 0.5},
        "parametry": {
            "tętno": (80, 130),
            "ciśnienie_skurczowe": (90, 150),
            "ciśnienie_rozkurczowe": (50, 90),
            "temperatura": (38.0, 40.0),
            "saturacja": (88, 96),
            "GCS": (13, 15),
            "ból": (3, 7),    # Ból przy oddychaniu
            "częstotliwość_oddechów": (20, 35),  # Przyspieszone!
            "czas_od_objawów_h": (12, 96)
        },
        "objawy": ["kaszel", "gorączka", "duszność", "ból w klatce piersiowej", "osłabienie"],
        "prawdopodobieństwa_triażu": [0.10, 0.50, 0.35, 0.05, 0.0],  # 50% kat 2
        "choroby_współistniejące": {
            "POChP": 0.3,
            "astma": 0.2
        },
        "typ": "internistyczny",
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "złamanie_kończyny": {
        "demografia": {"wiek": (5, 80), "płeć_M": 0.6},
        "parametry": {
            "tętno": (70, 110),
            "ciśnienie_skurczowe": (100, 150),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.5, 37.5),
            "saturacja": (96, 100),
            "GCS": (15, 15),  # Przytomny
            "ból": (6, 10),   # Bardzo boli!
            "częstotliwość_oddechów": (14, 20),
            "czas_od_objawów_h": (0.5, 24)
        },
        "objawy": ["ból", "obrzęk", "ograniczenie ruchu", "deformacja", "sine"],
        "prawdopodobieństwa_triażu": [0.0, 0.15, 0.65, 0.20, 0.0],  # 65% kat 3
        "choroby_współistniejące": {
            "osteoporoza": 0.3
        },
        "typ": "urazowy",
        "oddział_docelowy": ["Ortopedia", "SOR"]
    },
    
    "ból_brzucha": {
        "demografia": {"wiek": (10, 70), "płeć_M": 0.45},
        "parametry": {
            "tętno": (70, 100),
            "ciśnienie_skurczowe": (100, 140),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.5, 38.0),
            "saturacja": (96, 100),
            "GCS": (15, 15),
            "ból": (3, 7),    # Umiarkowany
            "częstotliwość_oddechów": (14, 20),
            "czas_od_objawów_h": (2, 48)
        },
        "objawy": ["ból brzucha", "nudności", "wzdęcia", "biegunka"],
        "prawdopodobieństwa_triażu": [0.0, 0.05, 0.35, 0.50, 0.10],  # 50% kat 4
        "choroby_współistniejące": {
            "zespół jelita drażliwego": 0.2
        },
        "typ": "internistyczny",
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "infekcja_górnych_dróg_oddechowych": {
        "demografia": {"wiek": (1, 60), "płeć_M": 0.5},
        "parametry": {
            "tętno": (70, 95),
            "ciśnienie_skurczowe": (100, 130),
            "ciśnienie_rozkurczowe": (60, 85),
            "temperatura": (37.0, 38.5),
            "saturacja": (96, 100),
            "GCS": (15, 15),
            "ból": (1, 4),    # Łagodny
            "częstotliwość_oddechów": (14, 20),
            "czas_od_objawów_h": (24, 120)
        },
        "objawy": ["kaszel", "katar", "ból gardła", "gorączka", "osłabienie"],
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.05, 0.30, 0.65],  # 65% kat 5!
        "choroby_współistniejące": {},
        "typ": "internistyczny",
        "oddział_docelowy": ["Interna", "SOR"]
    },
    
    "uraz_wielonarzadowy": {
        "demografia": {"wiek": (15, 60), "płeć_M": 0.7},
        "parametry": {
            "tętno": (100, 150),
            "ciśnienie_skurczowe": (70, 120),
            "ciśnienie_rozkurczowe": (40, 80),
            "temperatura": (35.5, 37.0),
            "saturacja": (80, 95),
            "GCS": (5, 14),   # NOWE - obniżone!
            "ból": (8, 10),   # Ekstremalny
            "częstotliwość_oddechów": (20, 40),  # Krytyczne
            "czas_od_objawów_h": (0.25, 2)  # Bardzo niedawno
        },
        "objawy": ["urazy wielonarządowe", "krwawienie", "zaburzenia świadomości", "wstrząs"],
        "prawdopodobieństwa_triażu": [0.95, 0.05, 0.0, 0.0, 0.0],  # 95% kat 1!!!
        "choroby_współistniejące": {},
        "typ": "urazowy",
        "oddział_docelowy": ["SOR", "Chirurgia"]
    },
    
    "migraine": {
        "demografia": {"wiek": (15, 60), "płeć_M": 0.3},
        "parametry": {
            "tętno": (70, 95),
            "ciśnienie_skurczowe": (100, 140),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.5, 37.5),
            "saturacja": (96, 100),
            "GCS": (15, 15),
            "ból": (6, 9),    # Silny ból głowy
            "częstotliwość_oddechów": (12, 18),
            "czas_od_objawów_h": (2, 24)
        },
        "objawy": ["silny ból głowy", "światłowstręt", "nudności", "wymioty"],
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.20, 0.60, 0.20],  # 60% kat 4
        "choroby_współistniejące": {
            "migrena": 0.8
        },
        "typ": "neurologiczny",
        "oddział_docelowy": ["Neurologia", "SOR"]
    },
    
    "skręcenie_stawu": {
        "demografia": {"wiek": (10, 50), "płeć_M": 0.6},
        "parametry": {
            "tętno": (70, 90),
            "ciśnienie_skurczowe": (100, 130),
            "ciśnienie_rozkurczowe": (60, 85),
            "temperatura": (36.5, 37.0),
            "saturacja": (98, 100),
            "GCS": (15, 15),
            "ból": (4, 7),    # Umiarkowany
            "częstotliwość_oddechów": (12, 16),
            "czas_od_objawów_h": (1, 48)
        },
        "objawy": ["ból", "obrzęk", "ograniczenie ruchu", "siniaki"],
        "prawdopodobieństwa_triażu": [0.0, 0.0, 0.10, 0.50, 0.40],  # 50% kat 4
        "choroby_współistniejące": {},
        "typ": "urazowy",
        "oddział_docelowy": ["Ortopedia", "SOR"]
    }
}

# Średni czas obsługi według kategorii
TRIAGE_SERVICE_TIMES = {
    1: 15,
    2: 30,
    3: 60,
    4: 90,
    5: 120
}

# Maksymalne czasy oczekiwania
TRIAGE_WAIT_TIMES = {
    1: 0,
    2: 10,
    3: 30,
    4: 60,
    5: 120
}
