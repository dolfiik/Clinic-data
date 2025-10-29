import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

env_path = backend_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f" Załadowano zmienne środowiskowe z {env_path}")
else:
    print(f" Nie znaleziono pliku .env w {env_path}")
    print(" Używam domyślnych wartości...")

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


def get_database_url():
    """Pobiera URL bazy danych ze zmiennych środowiskowych"""
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "clinic_secure_password_2025")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "clinic_db")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def generate_department_occupancy(hour, day_of_week):
    """
    Generuje realistyczne obłożenie oddziałów z uwzględnieniem sezonowości.
    
    Args:
        hour: Godzina dnia (0-23)
        day_of_week: Dzień tygodnia (0=Poniedziałek, 6=Niedziela)
        
    Returns:
        Dict z obłożeniem dla każdego oddziału
    """
    occupancy = {}
    is_weekend = day_of_week >= 5
    is_night = hour < 6 or hour >= 22
    is_peak_hours = 8 <= hour <= 20
    
    for dept, capacity in DEPARTMENT_CAPACITY.items():
        base_rate = random.uniform(0.3, 0.7)
        
        if dept == "SOR":
            base_rate = random.uniform(0.5, 0.85)
            if 18 <= hour <= 23:  # Wieczorny szczyt
                base_rate = min(0.95, base_rate + 0.15)
        
        if is_peak_hours and dept != "SOR":
            base_rate = min(0.90, base_rate + 0.20)
        
        if is_night and dept != "SOR":
            base_rate *= 0.6
        
        if is_weekend:
            if dept in ["Chirurgia", "Ortopedia", "Ginekologia"]:
                base_rate *= 0.70  # Dużo mniej planowych zabiegów
            elif dept != "SOR":
                base_rate *= 0.85
        
        if day_of_week == 0 and dept != "SOR":
            base_rate = min(0.95, base_rate + 0.10)
        
        noise = random.uniform(-0.05, 0.05)
        base_rate = max(0.1, min(0.98, base_rate + noise))
        
        occupancy[dept] = int(capacity * base_rate)
    
    return occupancy


def seed_database(days=7, hours_per_day=24):
    """
    Wypełnia bazę danych danymi obłożenia oddziałów.
    
    Args:
        days: Liczba dni wstecz do wygenerowania danych (domyślnie 7)
        hours_per_day: Liczba pomiarów na dzień (domyślnie 24 - co godzinę)
    """
    print("="*70)
    print("SEEDER BAZY DANYCH - OBŁOŻENIE ODDZIAŁÓW")
    print("="*70)
    
    database_url = get_database_url()
    print(f"\n📊 Łączenie z bazą danych...")
    
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        db.execute(text("SELECT 1"))
        print("Połączono z bazą danych")
        
    except Exception as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        return
    
    try:
        result = db.execute(text("DELETE FROM department_occupancy"))
        db.commit()
        print(f"✓ Usunięto {result.rowcount} starych wpisów")
    except Exception as e:
        print(f"⚠ Nie można wyczyścić starych danych: {e}")
        db.rollback()
    
    total_records = days * hours_per_day
    current_time = datetime.now()
    records_created = 0

    for day in range(days - 1, -1, -1):
        for hour in range(24):
            timestamp = current_time - timedelta(days=day, hours=(23 - hour))
            day_of_week = timestamp.weekday()
            
            occupancy = generate_department_occupancy(timestamp.hour, day_of_week)
            
            try:
                query = text("""
                    INSERT INTO department_occupancy (
                        timestamp, sor, interna, kardiologia, chirurgia,
                        ortopedia, neurologia, pediatria, ginekologia
                    ) VALUES (
                        :timestamp, :sor, :interna, :kardiologia, :chirurgia,
                        :ortopedia, :neurologia, :pediatria, :ginekologia
                    )
                """)
                
                db.execute(query, {
                    "timestamp": timestamp,
                    "sor": occupancy["SOR"],
                    "interna": occupancy["Interna"],
                    "kardiologia": occupancy["Kardiologia"],
                    "chirurgia": occupancy["Chirurgia"],
                    "ortopedia": occupancy["Ortopedia"],
                    "neurologia": occupancy["Neurologia"],
                    "pediatria": occupancy["Pediatria"],
                    "ginekologia": occupancy["Ginekologia"]
                })
                
                records_created += 1
                
                progress = records_created / total_records * 100
                bar_length = 40
                filled = int(bar_length * records_created / total_records)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"\r   [{bar}] {progress:.1f}% ({records_created}/{total_records})", end='')
                
            except Exception as e:
                print(f"\n❌ Błąd podczas wstawiania danych: {e}")
                db.rollback()
                continue
    
    try:
        db.commit()
        print(f"\n\n Pomyślnie utworzono {records_created} wpisów obłożenia oddziałów")
    except Exception as e:
        print(f"\n Błąd podczas zapisywania danych: {e}")
        db.rollback()
        return
    finally:
        db.close()
    
    db = SessionLocal()
    
    try:
        for dept, capacity in DEPARTMENT_CAPACITY.items():
            dept_key = dept.lower()
            result = db.execute(text(f"""
                SELECT 
                    AVG({dept_key}) as avg_occ,
                    MIN({dept_key}) as min_occ,
                    MAX({dept_key}) as max_occ
                FROM department_occupancy
            """))
            row = result.fetchone()
            avg_occ, min_occ, max_occ = row
            avg_percent = (avg_occ / capacity * 100) if capacity > 0 else 0
            
            print(f"   {dept:15} śr: {avg_occ:5.1f}/{capacity} ({avg_percent:5.1f}%)  "
                  f"min: {min_occ:2.0f}  max: {max_occ:2.0f}")
        
        result = db.execute(text("""
            SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest
            FROM department_occupancy
        """))
        row = result.fetchone()
        oldest, newest = row
        
       
    except Exception as e:
        print(f"\n Nie można pobrać statystyk: {e}")
    finally:
        db.close()
    

if __name__ == "__main__":
    seed_database(days=7, hours_per_day=24) 
