from decimal import Decimal
from datetime import datetime
from app.schemas import (
    PatientCreate,
    PatientUpdate,
    TriagePredictionCreate,
    DepartmentOccupancyCreate,
    AuditLogCreate
)

def test_patient_validation():
    """Test walidacji pacjenta"""
    # Poprawne dane
    try:
        patient = PatientCreate(
            wiek=67,
            plec="M",
            tetno=Decimal("125.0"),
            cisnienie_skurczowe=Decimal("95.0"),
            temperatura=Decimal("37.2"),
            saturacja=Decimal("88.0"),
            gcs=14,
            bol=9
        )
        print("Poprawne dane zaakceptowane")
        print(f"Wiek: {patient.wiek}, Płeć: {patient.plec}")
    except Exception as e:
        print(f" Błąd: {e}")
    
    # Niepoprawny wiek
    try:
        patient = PatientCreate(
            wiek=150,  # Za duży
            plec="M"
        )
        print("Zaakceptowano niepoprawny wiek!")
    except Exception as e:
        print(f"Odrzucono niepoprawny wiek (150): {type(e).__name__}")
    
    # Niepoprawna płeć
    try:
        patient = PatientCreate(
            wiek=67,
            plec="X"  # Tylko M lub K
        )
        print("Zaakceptowano niepoprawną płeć!")
    except Exception as e:
        print(f"Odrzucono niepoprawną płeć (X): {type(e).__name__}")
    
    # Niepoprawne tętno
    try:
        patient = PatientCreate(
            wiek=67,
            plec="M",
            tetno=Decimal("500.0")  # Za wysokie
        )
        print("Zaakceptowano niepoprawne tętno!")
    except Exception as e:
        print(f"Odrzucono niepoprawne tętno (500): {type(e).__name__}")

def test_patient_update():
    """Test częściowej aktualizacji"""
    try:
        # Tylko niektóre pola
        update = PatientUpdate(
            temperatura=Decimal("38.5"),
            status="w_leczeniu"
        )
        print(" Częściowa aktualizacja zaakceptowana")
        print(f"  Zaktualizowane pola: temperatura={update.temperatura}, status={update.status}")
        
        # Sprawdź exclude_unset
        data = update.model_dump(exclude_unset=True)
        print(f"Tylko ustawione pola: {list(data.keys())}")
        
    except Exception as e:
        print(f"Błąd: {e}")

def test_triage_prediction():
    """Test predykcji"""
    try:
        prediction = TriagePredictionCreate(
            patient_id=1,
            kategoria_triazu=1,
            prob_kat_1=Decimal("0.92"),
            prob_kat_2=Decimal("0.06"),
            prob_kat_3=Decimal("0.02"),
            prob_kat_4=Decimal("0.0"),
            prob_kat_5=Decimal("0.0"),
            przypisany_oddzial="Kardiologia",
            oddzial_docelowy="Kardiologia",
            model_version="rf_improved_20251017",
            confidence_score=Decimal("0.92")
        )
        print("Predykcja zaakceptowana")
        print(f"Kategoria: {prediction.kategoria_triazu}, Confidence: {prediction.confidence_score}")
    except Exception as e:
        print(f"Błąd: {e}")
    
    # Niepoprawna kategoria
    try:
        prediction = TriagePredictionCreate(
            patient_id=1,
            kategoria_triazu=6,  # Tylko 1-5
            prob_kat_1=Decimal("0.5"),
            prob_kat_2=Decimal("0.5"),
            prob_kat_3=Decimal("0.0"),
            prob_kat_4=Decimal("0.0"),
            prob_kat_5=Decimal("0.0"),
            przypisany_oddzial="SOR",
            model_version="test",
            confidence_score=Decimal("0.5")
        )
        print("Zaakceptowano niepoprawną kategorię!")
    except Exception as e:
        print(f"Odrzucono niepoprawną kategorię (6): {type(e).__name__}")

def test_department_occupancy():
    """Test obłożenia"""
    try:
        occupancy = DepartmentOccupancyCreate(
            timestamp=datetime.now(),
            sor=18,
            interna=35,
            kardiologia=22,
            chirurgia=28
        )
        print("Obłożenie zaakceptowane")
        print(f"SOR: {occupancy.sor}, Interna: {occupancy.interna}")
    except Exception as e:
        print(f"Błąd: {e}")
    
    # Niepoprawna wartość
    try:
        occupancy = DepartmentOccupancyCreate(
            timestamp=datetime.now(),
            sor=-5  # Nie może być ujemne
        )
        print("Zaakceptowano ujemne obłożenie!")
    except Exception as e:
        print(f"Odrzucono ujemne obłożenie: {type(e).__name__}")

def test_audit_log():
    """Test logu audytowego"""
    try:
        log = AuditLogCreate(
            user_id=1,
            action="CREATE_PATIENT",
            table_name="patients",
            record_id=1,
            new_values={"wiek": 67, "plec": "M"},
            ip_address="192.168.1.100"
        )
        print("Log zaakceptowany")
        print(f"Action: {log.action}, User: {log.user_id}")
    except Exception as e:
        print(f"Błąd: {e}")

if __name__ == "__main__":
    test_patient_validation()
    test_patient_update()
    test_triage_prediction()
    test_department_occupancy()
    test_audit_log()
