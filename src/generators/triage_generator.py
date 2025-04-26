import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import uuid

from ..config.constants import MEDICAL_CASE_TEMPLATES, DEPARTMENTS, DEPARTMENT_CAPACITY


class TriageDataGenerator:

    """
    Generator danych przypadkow triazu dla systemu wsopmagania decyzji placowki medycznej
    Wykorzystuje szablony przypadkow do generowania realistycznych danych
    """

    def __init__(self, templates, date_range=None):
        """
        Inicjalizacja generatora danych 
        args:
        templates (slownik) - slownik szablonow przypadkow medycznych
        date_range (tuple, opcjonalne) - zakres dat (start, koniec) do generowania realistycznych danych
        """

        self.templates = templates
        self.template_keys = list(templates.keys())

        #domyslny zakres dat
        if date_range is None:
            self.start_date = datetime(2025,1,1)
            self.end_date = datetime(2025,12,31)
        else:
            self.start_date, self.end_date = date_range


    def generate_random_case(self, specific_template=None, specific_date=None):

        """
        Funkcja generuje losowy przypadek medyczny na podstawie szablonu

        args:
        specific_template (str, opcjonalne): nazwa konkretnego szablonu do uzycia
        specific_date (datetime, opcjonalne): konkretna data/czas dla przpyadku
        
        zwraca:
        dict: slownik z danymi przypadku medycznego
        """

        #wybor losowego szablonu lub podanego
        template_name = specific_template if specific_template else np.random.choice(self.template_keys)
        template = self.templates[template_name]

        #generuj dane demograficzne
        age = np.random.randint(*template["demografia"]["wiek"])
        gender = "M" if np.random.random() < template["demografia"]["płeć_M"] else "K"

        #generuj parametry zycuiowe z fizjologicznymi korelacjami
        vital_params = self._generate_correlated_vitals(template, age, gender)

        #generuj objawy
        symptoms = self._generate_symptoms(template)

        #generuj choroby wspolistniejace
        comorbidities = self._generate_comorbidities(template, age, gender)

        triage_category = self._determine_triage_category(template, vital_params, age , symptoms, comorbidities)

        target_department = self._determine_department(template, vital_params, age, triage_category)

        #wygeneruj date przyjecia lub uzyj okreslonej
        admission_date = specific_date if specific_date else self._generate_random_timestamp()


        #kompletny przypadek
        case = {
            "id_przpadku": str(uuid.uuid4())[:8], #unikalne id 8 pierwsze znakow uuid
            "szablon_przypadku": template_name,
            "wiek": age,
            "płeć": gender,
            "data_przyjęcia": admission_date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(admission_date, datetime) else admission_date,
            "objawy": symptoms,
            "choroby_współistniejące": comorbidities if comorbidities else None,
            "oddział_docelowy": target_department,
            "kategoria_triażu": triage_category,
            **vital_params #rozpakowuje wszystkie parametry zyciowe
        }

        return case

    def _generate_correlated_vitals(self, template, age, gender):
        """
        Generuje skorelowane parametry zyciowe uwzgledniaajc wiek, plec i specyfike przypadku 
        args:
        tempalte (dict) - szablon przypadku medycznego
        age (int) - wiek pacjenta
        gender (str) - plec pacjenta

        zwraca:
        dict - slownik z parametrami zyciowymi
        """
        vitals = {}

        #generowanie podstawowych parametrow z przedzialow zdefiniowanych w szablonie
        for param, (min_val, max_val) in template["parametry"].items():

            #losowosc w rozkladzie
            avg = (min_val + max_val) / 2
            std = (max_val - min_val) / 6 # +/- 3 odchylenia standardowe pokrywaja caly zakres

            value = np.random.normal(avg, std)
            value = max(min_val, min(max_val, value))

            vitals[param] = round(value, 1)

        #modyfikacje zwiazane z wiekiem
        if age > 65:
            if "ciśnienie_skurczowe" in vitals:
                vitals["ciśnienie_skurczowe"] += np.random.randint(5, 15)
            if "ciśnienie_rozkurzczowe" in vitals:
                vitals["ciśnienie_rozkurzczowe"] += np.random.randint(3,8)
            if "saturacja" in vitals:
                vitals["saturacja"] = max(88, vitals["saturacja"] - np.random.randint(1,3))

        elif age < 12:
            #u dzieci czesto wyzsze tetno, nizsze cisnienie
            if "tętno" in vitals:
                vitals["tętno"] += np.random.randint(10,20)
            if "ciśnienie_skurczowe" in vitals:
                vitals["ciśnienie_skurczowe"] = max(80, vitals["ciśnienie_skurczowe"] - np.random.randint(5,15))
            if "ciśnienie_rozkurzczowe" in vitals:
                vitals["ciśnienie_rozkurzczowe"] = max(50, vitals["ciśnienie_rozkurzczowe"] - np.random.randint(5,10))

        #modyfikacje zwiazane z plcia
        if gender == "K":
            #kobiety czesto maja nieco nizsze cisnienie i wyzsze tetno
            if "ciśnienie_skurczowe" in vitals:
                vitals["ciśnienie_skurczowe"] = max(90,vitals["ciśnienie_skurczowe"] - np.random.randint(0,8))
            if "tętno" in vitals:
                vitals["tętno"] += np.random.randint(0,5)


        #korelacje miedzy parametrami zyciowymi 

        #1. miedzy goraczka a tetnem
        if "temperatura" in vitals and "tętno" in vitals:
            if vitals["temperatura"] > 38.0:
                #kazdy stopien powyzej 37 zwieksza tetno o okolo 10 uderzen
                fever_inc = (vitals["temperatura"] - 37.0) * 10
                vitals["tętno"] += round(fever_inc)

        #2. miedzy saturacja a czestosfcia oddechow
        if "saturacja" in vitals and "częstość_oddechów" in vitals:
            if vitals["saturacja"] < 92:
                #niska saturacja zwieksza czestosc oddechow
                vitals["częstość_oddechów"] += round((92 - vitals["saturacja"]) * 1.5)

        #3. miedzy bolem a tetnem i cisnieniem
        if "ból" in vitals:
            if "tętno" in vitals and vitals["ból"] > 6:
                #silny bol zwieksza tetno
                vitals["tętno"] += round((vitals["ból"] - 5) * 2)

            if "ciśnienie_skurczowe" in vitals and vitals["ból"] > 7:
                vitals["ciśnienie_skurczowe"] += round((vitals["ból"] - 6) * 3)

        #4 miedzy niskim cisnienim a wysokim tetnem (kompensacja)
        if "ciśnienie_skurczowe" in vitals and "tętno" in vitals:
            if vitals["ciśnienie_skurczowe"] < 100:
                #niskie cisnienie powoduje techykardie kompensacyjna
                vitals["tętno"] += round((100 - vitals["ciśnienie_skurczowe"]) * 0.5)

        # zaokraglenie wartrosci do odpowiedniej precyzji 
        for param in vitals:
            if param in ["tętno", "ciśnienie_skurczowe", "ciśnienie_rozkurzczowe", "częstość_oddechów", "GCS"]:
                vitals[param] = int(round(vitals[param]))
            else:
                vitals[param] = round(vitals[param], 1)

        return vitals


    def _generate_symptoms(self, template):

        """
        Generuje liste objawow z mozliwymi dodatokwymi objawami powiazanymi

        args:
        template (dict): szablon przypadku medycznego
        zwraca:
        str: lista objawow
        """

        base_symptoms = template.get("objawy", [])

        # losowa liczba objawow
        num_symptoms = np.random.randint(1, len(base_symptoms) + 1)
        selected_symptomps = np.random.choice(base_symptoms, size=num_symptoms, replace=False).tolist()

        related_symptomps_map = {
            "ból w klatce piersiowej": ["niepokój", "strach", "osłabienie"],
            "duszność": ["kaszel", "niepokój", "osłabienie"],
            "ból głowy": ["nudności", "światłowstręt", "zawroty głowy"],
            "gorączka": ["dreszcze", "bóle mięśniowe", "osłabienie"],
            "ból brzucha": ["nudności", "brak apetytu", "wzdęcia"],
            "nudności": ["wymioty", "ból brzucha", "brak apetytu"],
            "zawroty głowy": ["zaburzenia równowagi", "osłabienie", "ból głowy"],
            "wysypka": ["świąd", "gorączka", "ból"],
            "kaszel": ["ból gardła", "duszność", "odkrztuszanie wydzieliny"],
            "omdlenie": ["zawroty głowy", "osłabienie", "pocenie się"],
            "krwawienie": ["osłabienie", "zawroty głowy", "niepokój"],
            "złamanie": ["ból", "obrzęk", "ograniczenie ruchomości"]
        }

        for symptom in selected_symptomps.copy(): #kopia zeby moc modyfkiowac oryginal w petli
            if symptom in related_symptomps_map:
                for related in related_symptomps_map[symptom]:
                    if np.random.random() < 0.4: #40% szans na dodatokwy objaw
                        if related not in selected_symptomps:
                            selected_symptomps.append(related)


        return ",".join(selected_symptomps)

    def _generate_comorbidities(self, template, age, gender):
        """
        generuje liste chorob wspolistniejacych
        args:
        template (dict): szablon przypadku medycznego
        age (int) - wiek pacjenta
        gender(str) - plec pacjenta
        zwraca:
        str: lista chorob wspolisnitejacych rozdzielona przecinkami
        """

        comorbidities = []

        #dodaj choroby z szablonu
        template_comorbidities = template.get("choroby_współistniejące", {})
        for disease, prob in template_comorbidities.items():
            if np.random.random() < prob:
                comorbidities.append(disease)


        #dodatkowe choroby zalezne od wieku
        age_related_comorbidities = {
            (60, 120): {  # 60+ lat
                "nadciśnienie": 0.5,
                "cukrzyca typu 2": 0.3,
                "choroba wieńcowa": 0.25,
                "osteoporoza": 0.2,
                "przewlekła choroba nerek": 0.15,
                "demencja": 0.1
            },
            (40, 59): {  # 40-59 lat
                "nadciśnienie": 0.3,
                "cukrzyca typu 2": 0.15,
                "hipercholesterolemia": 0.2,
                "otyłość": 0.2
            },
            (18, 39): {  # 18-39 lat
                "alergie": 0.2,
                "astma": 0.1,
                "depresja": 0.1,
                "otyłość": 0.15
            },
            (0, 17): {  # 0-17 lat
                "alergie": 0.15,
                "astma": 0.08,
                "ADHD": 0.05
            }
        }

        #dodawnie chorob zaleznych od wieku
        for age_range, diseases in age_related_comorbidities.items():
            if age_range[0] <= age <= age_range[1]:
                for disease, prob in diseases.items():
                    if np.random.random() < prob and disease not in comorbidities:
                        comorbidities.append(disease)


        #dodwanie chorob zaleznych od plci
        gender_related_comorbidities = {
            "M": {
                "przerost prostaty": lambda age: 0.3 if age > 60 else 0.0,
                "choroba wieńcowa": lambda age: 0.2 if age > 45 else 0.05
            },
            "K": {
                "osteoporoza": lambda age: 0.3 if age > 60 else 0.0,
                "niedokrwistość": lambda age: 0.2 if 15 <= age <= 50 else 0.1,
                "migrena": lambda age: 0.15 if 18 <= age <= 55 else 0.05
            }
        }

        if gender in gender_related_comorbidities:
            for disease, prob_func in gender_related_comorbidities[gender].items():
                prob = prob_func(age)
                if np.random.random() < prob and disease not in comorbidities:
                    comorbidities.append(disease)

        return ",".join(comorbidities) if comorbidities else None

    
    def _determine_triage_category(self, template, vital_params, age, symptoms, comorbidities):
        """
        Okresla kategorie triazu z uwzglednieniem parametrow zyciowych i czynnikow ryzyka
        args:
        template(dict) - szablon przypadku medycznego
        vital_params(dict) - parametry zyciowe
        age(int) - wiek pacjenta
        symptoms(str) - lista objawow
        comorbidities(str) - lista chorob wspolisnitejacych
        zwraca:
        int: kategoria triazy (1-5, gdzie 1 jest najbardziej pilna)
        """

        #bazowe prawdopodobienstwa z szablonu
        base_probs = template["prawdopodobieństwa_triażu"].copy()
        modified_probs = base_probs.copy()

        #modyfikacja na podstawie parametrow zyciowych - krytyczne wartosci

        #reguly podwyzszajace pilnosc do kategorii 1 (stan krytyczny)
        if any([
            vital_params.get("saturacja", 100) < 90,
            vital_params.get("tętno", 80) > 150 or vital_params.get("tętno", 80) < 40,
            vital_params.get("ciśnienie_skurczowe", 120) < 80,
            vital_params.get("temperatura", 37) > 40,
            vital_params.get("GCS", 15) < 9
        ]):
            return 1

        #reguly podwyzszajace pilnosc do kategorii 2 (bardzo pilne)
        if any([
            vital_params.get("saturacja", 100) < 92,
            vital_params.get("tętno", 80) > 130 or vital_params.get("tętno", 80) < 50,
            vital_params.get("ciśnienie_skurczowe", 120) < 90 or vital_params.get("ciśnienie_skurczowe", 120) > 200,
            vital_params.get("ciśnienie_rozkurczowe", 80) > 120,
            vital_params.get("temperatura", 37) > 39,
            vital_params.get("GCS", 15) < 13,
            vital_params.get("ból", 5) > 8
        ]):
            modified_probs[0] += 0.1
            modified_probs[1] += 0.3


        #reguly podwyzszajace pilnosc na podstawie objawow
        critical_symptoms = ["duszność", "ból w klatce piersiowej", "asymetria twarzy",
                             "zaburzenia mowy", "objawy otrzewnowe", "mnogie urazy", "krwawe wymioty", "drgawki"]


        for symptom in critical_symptoms:
            if symptoms and symptom in symptoms:
                modified_probs[0] += 0.1 # zwiekszenie szansy na kategorie 1
                modified_probs[1] += 0.1 # zwiekszenie szansy na kategorie 2


        if age > 75 or age < 3:
            modified_probs[0] += 0.05
            modified_probs[1] += 0.1
            modified_probs[2] += 0.05


        #choroby wspolistniejace zwiekszajace ryzyko
        high_risk_comorbidities = ["niewydolność serca", "przewlekła choroba nerek", "choroba wieńcowa", "udar w wywiadzie",
                                   "cukrzyca", "POChP", "immunosupresja","nowotwór"]

        if comorbidities:
            for disease in high_risk_comorbidities:
                if disease in comorbidities:
                    modified_probs[0] += 0.05
                    modified_probs[1] += 0.05

        #normalizacja prawdopodobienstw
        total = sum(modified_probs)
        modified_probs = [p/total for p in modified_probs]

        #wybor kategorii triazu na podstawie zmodyfikowanych prawdopodobienstw
        category = np.random.choice(range(1,6), p=modified_probs)

        return category


    def _determine_department(self, template, vital_params, age, triage_category):
        """
        Przypisuje oddzial docelowy na podstawie typu przypadku i parametrow pacjenta
        args:
        template (dict) - szablon przypadku medycznego
        vital_params (dict) - parametry zyciowe
        age (int) - wiek pacjenta
        triage_category (int) - kategoria triazu
        zwraca:
        str - oddzial docelowy
        """

        target_departments = template.get("oddział_docelowy", ["SOR"])

        if triage_category == 1:
            return "SOR"


        #dzieci < 18 kierowane sa na pediatrie (jesli jest dostepna)
        if age < 18 and "Pediatria" in target_departments:
            return "Pediatria"
        elif age < 18 and "Pediatria" not in target_departments:
            if "Pediatria" in DEPARTMENTS:
                return "Pediatria"

        if template.get("typ") == "ortopedyczny" and "Ortopedia" in DEPARTMENTS:
            return "Ortopedia"


        weights = []
        for i in range(len(target_departments)):
            #pierwszy oddzial ma wage 0.6, drugi 0.3, trzeci i kolejne po 0.1
            if i == 0:
                weights.append(0.6)
            elif i == 1:
                weights.append(0.3)
            else:
                weights.append(0.1 / (len(target_departments) - 2)) if len(target_departments) > 2 else weights.append(0.1)



        #normalizacja wag
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]

        #losowy wybor na podstawie wag
        return np.random.choice(target_departments, p=weights)

    
    def _generate_random_timestamp(self):
        """
        Generuje losowy timestamp z uwzglednieniem rozkladu dziennego i tygodniowego

        zwraca:
        datetime: losowa data i czas
        """

        days_range = (self.end_date - self.start_date).days
        random_day = np.random.randint(0, days_range + 1)
        random_date = self.start_date + timedelta(days=random_day)

        hourly_weights = [
            3, 2, 2, 1, 1, 2,  # 00: 00 - 05:59
            3, 5, 7, 8, 9, 10, # 06:00 - 11:59
            9, 8, 8, 8, 9, 10, #12:00 - 17:59
            9, 8, 7, 6, 5, 4   #18:00 - 23:59
        ]

        #modyfikacja wag w zaleznosci od dnia tygodnia
        day_of_week = random_date.weekday()
        if day_of_week >= 5: #weekend
            #mniej przyjec w weekend, ale bardziej rownomiernie rozlozone
            hourly_weights = [w * 0.6 if (6 <= i <= 18) else w *0.8 for i, w in enumerate(hourly_weights)]
        elif day_of_week == 0:
            #wiecej przyjec w poniedzialek rano
            hourly_weights = [w * 1.2 if (8 <= i < 12) else w for i, w in enumerate(hourly_weights)]

        #normalizacja wag
        hourly_weights = [w/sum(hourly_weights) for w in hourly_weights]

        hour = np.random.choice(range(24), p=hourly_weights)
        minute = np.random.randint(0, 60)
        second = np.random.randint(0,60)

        return random_date.replace(hour=hour, minute=minute, second=second)


    def generate_dataset(self, num_cases=1500, balance_categories=True, balance_departments=True):
        """
        Generuje pelny zestaw danych triazu
        args:
        num_cases (int) - liczba przypadkow do wygenerowania
        balance_categories (bool) - czy zrownowazyc kategorie triazu
        balance_departments (bool) - czy zrownowazyc oddzialy docelowe
        zwraca:
        pd.DataFrame: DataFrame z wygenrowanymi danymi
        """

        cases = []

        if balance_categories or balance_departments:
            #generowanie z uwzglednieniem rownoazenia

            #realistyczny rozklad kategorii triazu
            desired_triage_distribution = {
                1: 0.10, #10% dla kategeorii 1
                2: 0.25, #25% dla 2
                3: 0.40, #40% dla 3
                4: 0.20, #20% dla 4
                5: 0.05 #5% dla 5
            }

            department_capacities = {dept: DEPARTMENT_CAPACITY.get(dept, 30) for dept in DEPARTMENTS}
            total_capacity = sum(department_capacities.values())
            desired_department_distribution = {
                dept: capacity / total_capacity for dept, capacity in department_capacities.items()
            }

            triage_counts = {cat: 0 for cat in range(1,6)}
            department_counts = {dept: 0 for dept  in DEPARTMENTS}

            for i in range(num_cases):
                #sprawdzenie aktualnego rozlkadu i okreslenie pozadanej kategorii/oddzialu
                current_triage_dist = {cat: count/max(1,i) for cat,count in triage_counts.items()}
                current_dept_dist = {dept: count/max(1,i) for dept, count in department_counts.items()}
                
                #najmniej reprezentowane kategorie i oddzialy
                triage_diff = {cat: desired_triage_distribution[cat] - current_triage_dist.get(cat,0) for cat in desired_triage_distribution}
                dept_diff = {dept: desired_department_distribution[dept] - current_dept_dist.get(dept,0) for dept in desired_department_distribution}
            
                target_triage = max(triage_diff.keys(), key=lambda k: triage_diff[k]) if balance_categories else None
                target_dept = max(dept_diff.keys(), key=lambda k: dept_diff[k]) if balance_departments else None

                #generuj przypadki, az trafisz na taki o odpowiednij kategorii/oddziale
                max_attempts = 20
                attempts = 0

                while attempts < max_attempts:
                    case = self.generate_random_case()
                    triage_match = not balance_categories or case["kategoria_triażu"] == target_triage
                    dept_match = not balance_categories or case["oddział_docelowy"] == target_dept

                    if triage_match and dept_match:
                        cases.append(case)
                        triage_counts[case["kategoria_triażu"]] = triage_counts.get(case["kategoria_triażu"],0) + 1
                        department_counts[case["oddział_docelowy"]] = department_counts.get(case["oddział_docelowy"],0) + 1
                        break

                    attempts += 1

                if attempts == max_attempts:
                    #jesli nie znaleziono dokladnego dopasowania, dodaj najlepszu mozliwy
                    case = self.generate_random_case()
                    cases.append(case)
                    triage_counts[case["kategoria_triażu"]] = triage_counts.get(case["kategoria_triażu"], 0) + 1
                    department_counts[case["oddział_docelowy"]] = department_counts.get(case["oddział_docelowy"],0) + 1

        else:
            #geneorwanie bez rownoazenia
            for _ in range(num_cases):
                cases.append(self.generate_random_case())


        df = pd.DataFrame(cases)
        return df



if __name__ == '__main__':
    from ..config.constants import MEDICAL_CASE_TEMPLATES, DEPARTMENTS, DEPARTMENT_CAPACITY

    generator = TriageDataGenerator(MEDICAL_CASE_TEMPLATES)
    df = generator.generate_dataset(num_cases=1500, balance_categories=True)

    output_file = "data/raw/triage_data.csv"
    df.to_csv(output_file, index=False)
    print(f"Dane zapisane do: {output_file}")




