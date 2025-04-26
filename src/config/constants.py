"""
Stale i definicje dla generatora danych systemu
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
    "SOR" : 25,
    "Interna": 50,
    "Kardiologia": 30,
    "Chirurgia" : 35,
    "Ortopedia" : 25,
    "Neurologia" : 20,
    "Pediatria": 30,
    "Ginekologia": 20
}

SEASONAL_FACTORS = {
    "monthly" : {
        1: 1.3,
        2: 1.25,
        3: 1.15,
        4: 1.0,
        5: 0.9,
        6: 0.85,
        7: 0.8,
        8: 0.85,
        9: 0.95,
        10: 1.05,
        11: 1.15,
        12: 1.2
    },
    "weekly": {
        0: 1.3,  #duzy ruch w poniedzialek
        1: 1.1,
        2: 1.0,
        3: 0.95,
        4: 1.15,
        5: 0.7,
        6: 0.65 # niedziela najmniejszy ruch
    }
}


POLISH_HOLIDAYS = [
    (1,1), #nowy rok
    (1,6), #trzech kroli
    (5,1), #swieto pracy
    (5,3), #3maja
    (8,15), #wniebowziecie
    (11,1), #wszystkich swietych
    (11,11), #niepodleglosc
    (12,25), #bozenarodzenie 1
    (12,26) #bozenarodzenie 2
]



#szablony przypadkow medycznych (20)
"""

Demogragia: 
wiek - zakres (min, max) wieku pacjentow typowych dla danego schorzenia
plec_m - prawdopodobienstwo wystapienia tego schorzenia u mezczyzn - 0.6 - 60%

Parametry:
tetno, cisnienie, temperatura - jako pary (min,max)
bol - zakres intensywnosci (skala 1-10)
GCS - skala Glasgow w przypadkach neurologicznych (3-15)


Objawy:
lista typowych objawow zwiazanych z danym schorzeniem


Prawdopodobieństwa_triażu:
5 wartosci prawdopodovienstwa przypisania kategorii triazu (1-5)


Choroby wspolistniejace:
choroby towarzyszace z prawdopodobienstwem ich wystapienia

Typ:
specjalizacja medyczna przypadku (np. kardiologiczny, neurologiczny)

Oddzial docelowy:
lista potencjalnych oddzialow docelowych w kolejnosci pierszenstwa
"""


MEDICAL_CASE_TEMPLATES = {
    "bol_w_klatce": {
            "demografia": {"wiek": (45, 85), "płeć_M": 0.6},
            "parametry": {
                "tętno": (70, 120),
                "ciśnienie_skurczowe": (100, 190),
                "ciśnienie_rozkurczowe": (60, 110),
                "temperatura": (36.0, 37.8),
                "saturacja": (92, 99),
                "ból": (5, 10)
            },
            "objawy": ["ból w klatce piersiowej", "duszność", "potliwość", "osłabienie", "niepokój"],
            "prawdopodobieństwa_triażu": [0.15, 0.50, 0.25, 0.10, 0.0],  # kategorie 1-5
            "choroby_współistniejące": {
                "nadciśnienie": 0.6, 
                "cukrzyca": 0.3, 
                "choroba wieńcowa": 0.4,
                "hipercholesterolemia": 0.5
            },
            "typ": "kardiologiczny",
            "oddział_docelowy": ["Kardiologia", "SOR", "Interna"]
        },

    "udar": {
        "demografia": {"wiek": (55, 90), "płeć_M": 0.55},
        "parametry": {
            "tętno": (60, 110),
            "ciśnienie_skurczowe": (110, 220),
            "ciśnienie_rozkurczowe": (70, 115),
            "temperatura": (36.0, 37.5),
            "saturacja": (94, 100),
            "GCS": (3, 15)
        },
        "objawy": ["asymetria twarzy", "zaburzenia mowy", "niedowład kończyn", "zaburzenia równowagi", "ból głowy", "zawroty głowy"],
        "prawdopodobieństwa_triażu": [0.5, 0.4, 0.1, 0.0, 0.0],
        "choroby_współistniejące": {
            "nadciśnienie": 0.7, 
            "migotanie przedsionków": 0.3, 
            "cukrzyca": 0.35,
            "przebyty udar": 0.2
        },
        "typ": "neurologiczny",
        "oddział_docelowy": ["Neurologia", "SOR"]
    },


    "zlamanie_konczyny": {
        "demografia": {"wiek": (8, 90), "płeć_M": 0.55},
        "parametry": {
            "tętno": (60, 100),
            "ciśnienie_skurczowe": (100, 160),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.0, 37.0),
            "saturacja": (96, 100),
            "ból": (5, 10)
        },
        "objawy": ["ból kończyny", "obrzęk", "krwiak", "ograniczenie ruchomości", "zniekształcenie"],
        "prawdopodobieństwa_triażu": [0.05, 0.2, 0.6, 0.15, 0.0],
        "choroby_współistniejące": {
            "osteoporoza": 0.3, 
            "cukrzyca": 0.15
        },
        "typ": "ortopedyczny",
        "oddział_docelowy": ["Ortopedia", "SOR", "Chirurgia"]
    },


    "zapalenie_wyrostka": {
        "demografia": {"wiek": (5, 50), "płeć_M": 0.5},
        "parametry": {
            "tętno": (80, 120),
            "ciśnienie_skurczowe": (100, 160),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (37.5, 39.0),
            "saturacja": (96, 100),
            "ból": (6, 10)
        },
        "objawy": ["ból brzucha", "nudności", "wymioty", "brak apetytu", "tkliwość prawego dołu biodrowego", "objawy otrzewnowe"],
        "prawdopodobieństwa_triażu": [0.1, 0.4, 0.5, 0.0, 0.0],
        "choroby_współistniejące": {},
        "typ": "chirurgiczny",
        "oddział_docelowy": ["Chirurgia", "SOR"]
    },

    "zapalenie_pluc": {
        "demografia": {"wiek": (1, 95), "płeć_M": 0.5},
        "parametry": {
            "tętno": (80, 120),
            "ciśnienie_skurczowe": (90, 160),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (38.0, 40.0),
            "saturacja": (88, 96),
            "częstość_oddechów": (18, 30)
        },
        "objawy": ["kaszel", "duszność", "gorączka", "ból w klatce piersiowej", "osłabienie", "odkrztuszanie plwociny"],
        "prawdopodobieństwa_triażu": [0.1, 0.3, 0.4, 0.2, 0.0],
        "choroby_współistniejące": {
            "POChP": 0.3, 
            "astma": 0.2, 
            "cukrzyca": 0.15
        },
        "typ": "pulmonologiczny",
        "oddział_docelowy": ["Interna", "SOR"]
    },

    "zaostrzenie_astmy": {
        "demografia": {"wiek": (5, 65), "płeć_M": 0.45},
        "parametry": {
            "tętno": (90, 140),
            "ciśnienie_skurczowe": (100, 170),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.5, 37.8),
            "saturacja": (85, 95),
            "częstość_oddechów": (22, 36)
        },
        "objawy": ["duszność", "świszczący oddech", "kaszel", "ucisk w klatce piersiowej", "niepokój"],
        "prawdopodobieństwa_triażu": [0.15, 0.35, 0.4, 0.1, 0.0],
        "choroby_współistniejące": {
            "astma": 1.0, 
            "alergie": 0.6
        },
        "typ": "pulmonologiczny",
        "oddział_docelowy": ["Interna", "SOR", "Pediatria"]
    },


    "infekcja_ukladu_moczowego": {
        "demografia": {"wiek": (18, 90), "płeć_M": 0.2},
        "parametry": {
            "tętno": (70, 100),
            "ciśnienie_skurczowe": (100, 150),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (37.5, 39.0),
            "saturacja": (96, 100),
            "ból": (4, 8)
        },
        "objawy": ["ból przy oddawaniu moczu", "częstomocz", "ból podbrzusza", "gorączka", "zmętnienie moczu"],
        "prawdopodobieństwa_triażu": [0.05, 0.15, 0.4, 0.3, 0.1],
        "choroby_współistniejące": {
            "cukrzyca": 0.2, 
            "kamica nerkowa": 0.15,
            "przerost prostaty": 0.3
        },
        "typ": "urologiczny",
        "oddział_docelowy": ["Interna", "SOR"]
    },


    "uraz_glowy": {
        "demografia": {"wiek": (5, 80), "płeć_M": 0.6},
        "parametry": {
            "tętno": (60, 110),
            "ciśnienie_skurczowe": (100, 180),
            "ciśnienie_rozkurczowe": (60, 100),
            "temperatura": (36.0, 37.5),
            "saturacja": (95, 100),
            "GCS": (3, 15),
            "ból": (2, 9)
        },
        "objawy": ["uraz głowy", "ból głowy", "nudności", "wymioty", "zawroty głowy", "zaburzenia świadomości", "amnezja"],
        "prawdopodobieństwa_triażu": [0.2, 0.3, 0.3, 0.2, 0.0],
        "choroby_współistniejące": {},
        "typ": "neurologiczny/urazowy",
        "oddział_docelowy": ["Neurologia", "SOR", "Chirurgia"]
    },


    "bol_brzucha": {
        "demografia": {"wiek": (5, 95), "płeć_M": 0.45},
        "parametry": {
            "tętno": (60, 110),
            "ciśnienie_skurczowe": (100, 160),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.5, 38.5),
            "saturacja": (96, 100),
            "ból": (3, 9)
        },
        "objawy": ["ból brzucha", "nudności", "wymioty", "biegunka", "zaparcie", "brak apetytu", "wzdęcia"],
        "prawdopodobieństwa_triażu": [0.05, 0.2, 0.4, 0.3, 0.05],
        "choroby_współistniejące": {
            "zespół jelita drażliwego": 0.2, 
            "wrzody żołądka": 0.15, 
            "refluks": 0.25,
            "kamica żółciowa": 0.1
        },
        "typ": "gastroenterologiczny",
        "oddział_docelowy": ["Interna", "SOR", "Chirurgia"]
    },

    "zatrucie_pokarmowe": {
        "demografia": {"wiek": (2, 90), "płeć_M": 0.5},
        "parametry": {
            "tętno": (70, 120),
            "ciśnienie_skurczowe": (90, 150),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.5, 38.5),
            "saturacja": (96, 100)
        },
        "objawy": ["wymioty", "biegunka", "ból brzucha", "nudności", "gorączka", "osłabienie", "odwodnienie"],
        "prawdopodobieństwa_triażu": [0.05, 0.15, 0.4, 0.3, 0.1],
        "choroby_współistniejące": {},
        "typ": "gastroenterologiczny",
        "oddział_docelowy": ["Interna", "SOR", "Pediatria"]
    },

    "krwawienie_z_przewodu_pokarmowego": {
        "demografia": {"wiek": (40, 90), "płeć_M": 0.6},
        "parametry": {
            "tętno": (80, 140),
            "ciśnienie_skurczowe": (80, 150),
            "ciśnienie_rozkurczowe": (50, 90),
            "temperatura": (36.0, 37.5),
            "saturacja": (92, 99),
            "hemoglobina": (6, 12)
        },
        "objawy": ["krwawe wymioty", "smoliste stolce", "ból brzucha", "osłabienie", "zawroty głowy", "bladość", "omdlenie"],
        "prawdopodobieństwa_triażu": [0.3, 0.5, 0.2, 0.0, 0.0],
        "choroby_współistniejące": {
            "choroba wrzodowa": 0.4, 
            "marskość wątroby": 0.2,
            "przyjmowanie NLPZ": 0.5
        },
        "typ": "gastroenterologiczny",
        "oddział_docelowy": ["Chirurgia", "SOR", "Interna"]
    },


     "migrena": {
        "demografia": {"wiek": (15, 60), "płeć_M": 0.3},
        "parametry": {
            "tętno": (60, 100),
            "ciśnienie_skurczowe": (100, 160),
            "ciśnienie_rozkurczowe": (60, 90),
            "temperatura": (36.0, 37.2),
            "saturacja": (97, 100),
            "ból": (6, 10)
        },
        "objawy": ["ból głowy", "nadwrażliwość na światło", "nadwrażliwość na dźwięk", "nudności", "wymioty", "aura wzrokowa"],
        "prawdopodobieństwa_triażu": [0.05, 0.15, 0.5, 0.3, 0.0],
        "choroby_współistniejące": {
            "migrena": 0.9
        },
        "typ": "neurologiczny",
        "oddział_docelowy": ["Neurologia", "SOR"]
    },

    "zaostrzenie_pochp": {
        "demografia": {"wiek": (50, 90), "płeć_M": 0.7},
        "parametry": {
            "tętno": (90, 140),
            "ciśnienie_skurczowe": (110, 170),
            "ciśnienie_rozkurczowe": (60, 95),
            "temperatura": (36.0, 38.5),
            "saturacja": (80, 92),
            "częstość_oddechów": (22, 35)
        },
        "objawy": ["duszność", "kaszel", "odkrztuszanie wydzieliny", "obrzęki kończyn dolnych", "sinica", "osłabienie"],
        "prawdopodobieństwa_triażu": [0.15, 0.45, 0.35, 0.05, 0.0],
        "choroby_współistniejące": {
            "POChP": 1.0, 
            "nadciśnienie": 0.6, 
            "niewydolność serca": 0.4,
            "palenie papierosów": 0.8
        },
        "typ": "pulmonologiczny",
        "oddział_docelowy": ["Interna", "SOR"]
    },


    "omdlenie": {
        "demografia": {"wiek": (15, 90), "płeć_M": 0.4},
        "parametry": {
            "tętno": (50, 110),
            "ciśnienie_skurczowe": (90, 160),
            "ciśnienie_rozkurczowe": (50, 90),
            "temperatura": (36.0, 37.2),
            "saturacja": (95, 100),
            "poziom_cukru": (50, 130)
        },
        "objawy": ["omdlenie", "zawroty głowy", "osłabienie", "bladość", "pocenie się", "nudności"],
        "prawdopodobieństwa_triażu": [0.1, 0.3, 0.5, 0.1, 0.0],
        "choroby_współistniejące": {
            "nadciśnienie": 0.3, 
            "cukrzyca": 0.2, 
            "arytmia": 0.2
        },
        "typ": "kardiologiczny/neurologiczny",
        "oddział_docelowy": ["SOR", "Kardiologia", "Neurologia"]
    },

    "reakcja_alergiczna": {
        "demografia": {"wiek": (2, 70), "płeć_M": 0.5},
        "parametry": {
            "tętno": (70, 140),
            "ciśnienie_skurczowe": (80, 160),
            "ciśnienie_rozkurczowe": (50, 90),
            "temperatura": (36.0, 37.5),
            "saturacja": (88, 100)
        },
        "objawy": ["wysypka", "świąd", "obrzęk", "duszność", "chrypka", "ból gardła", "zawroty głowy"],
        "prawdopodobieństwa_triażu": [0.15, 0.35, 0.4, 0.1, 0.0],
        "choroby_współistniejące": {
            "alergie": 0.9, 
            "astma": 0.3
        },
        "typ": "alergologiczny",
        "oddział_docelowy": ["SOR", "Interna", "Pediatria"]
    },


    "napad_padaczkowy": {
        "demografia": {"wiek": (5, 70), "płeć_M": 0.55},
        "parametry": {
            "tętno": (70, 130),
            "ciśnienie_skurczowe": (100, 180),
            "ciśnienie_rozkurczowe": (60, 100),
            "temperatura": (36.0, 38.0),
            "saturacja": (92, 100),
            "GCS": (3, 15)
        },
        "objawy": ["drgawki", "zaburzenia świadomości", "senność", "ból głowy", "przygryzienie języka", "mimowolne oddanie moczu"],
        "prawdopodobieństwa_triażu": [0.2, 0.4, 0.3, 0.1, 0.0],
        "choroby_współistniejące": {
            "padaczka": 0.7, 
            "uraz głowy w przeszłości": 0.2
        },
        "typ": "neurologiczny",
        "oddział_docelowy": ["Neurologia", "SOR"]
    },

    "silne_krwawienie": {
        "demografia": {"wiek": (18, 90), "płeć_M": 0.55},
        "parametry": {
            "tętno": (90, 150),
            "ciśnienie_skurczowe": (70, 130),
            "ciśnienie_rozkurczowe": (40, 80),
            "temperatura": (36.0, 37.0),
            "saturacja": (90, 100),
            "hemoglobina": (5, 11)
        },
        "objawy": ["krwawienie", "zawroty głowy", "osłabienie", "bladość", "pocenie się", "omdlenie"],
        "prawdopodobieństwa_triażu": [0.4, 0.4, 0.2, 0.0, 0.0],
        "choroby_współistniejące": {
            "przyjmowanie leków przeciwkrzepliwych": 0.4
        },
        "typ": "chirurgiczny/urazowy",
        "oddział_docelowy": ["SOR", "Chirurgia"]
    },

    "uraz_wielonarzadowy": {
        "demografia": {"wiek": (15, 80), "płeć_M": 0.7},
        "parametry": {
            "tętno": (90, 160),
            "ciśnienie_skurczowe": (60, 140),
            "ciśnienie_rozkurczowe": (40, 90),
            "temperatura": (35.0, 37.0),
            "saturacja": (85, 98),
            "GCS": (3, 15),
            "ból": (7, 10)
        },
        "objawy": ["mnogie urazy", "ból", "krwawienie", "zaburzenia świadomości", "duszność", "bladość"],
        "prawdopodobieństwa_triażu": [0.7, 0.3, 0.0, 0.0, 0.0],
        "choroby_współistniejące": {},
        "typ": "urazowy",
        "oddział_docelowy": ["SOR", "Chirurgia", "Ortopedia"]
    },

    "zaburzenia_rytmu_serca": {
        "demografia": {"wiek": (50, 90), "płeć_M": 0.5},
        "parametry": {
            "tętno": (40, 180),
            "ciśnienie_skurczowe": (90, 180),
            "ciśnienie_rozkurczowe": (50, 100),
            "temperatura": (36.0, 37.5),
            "saturacja": (92, 99)
        },
        "objawy": ["kołatanie serca", "zawroty głowy", "omdlenie", "duszność", "ból w klatce piersiowej", "osłabienie"],
        "prawdopodobieństwa_triażu": [0.2, 0.4, 0.3, 0.1, 0.0],
        "choroby_współistniejące": {
            "nadciśnienie": 0.6, 
            "choroba wieńcowa": 0.4, 
            "niewydolność serca": 0.3,
            "migotanie przedsionków": 0.4
        },
        "typ": "kardiologiczny",
        "oddział_docelowy": ["Kardiologia", "SOR", "Interna"]
    },

    "zapalenie_opon_mozgowych": {
        "demografia": {"wiek": (1, 60), "płeć_M": 0.5},
        "parametry": {
            "tętno": (90, 150),
            "ciśnienie_skurczowe": (100, 180),
            "ciśnienie_rozkurczowe": (60, 100),
            "temperatura": (38.5, 41.0),
            "saturacja": (94, 100),
            "GCS": (5, 15)
        },
        "objawy": ["gorączka", "sztywność karku", "ból głowy", "wymioty", "wysypka", "światłowstręt", "zaburzenia świadomości"],
        "prawdopodobieństwa_triażu": [0.6, 0.3, 0.1, 0.0, 0.0],
        "choroby_współistniejące": {},
        "typ": "neurologiczny/infekcyjny",
        "oddział_docelowy": ["Neurologia", "SOR", "Interna", "Pediatria"]
    }
}

#sredni czas obslugi w minutach wedlug kategorii triazu
TRIAGE_SERVICE_TIMES = {
    1: 15, #Kategoria 1 - natychmiastowa pomoc
    2: 30, #Kategoria 2 - pilna pomoc
    3: 60, #Kategoria 3 - srednia pomoc
    4: 90, #Kategoria 4 - malo pikna pomoc
    5: 120, #Kategoria 5 - niepilna
}


#maksymalne czasy oczekiwania w minutach wedlug kategorii triazu

TRIAGE_WAIT_TIMES = {
    1: 0, #dla pierwszej kategorii natychmiastowa pomoc
    2: 10,
    3: 30,
    4: 60,
    5: 120
}
