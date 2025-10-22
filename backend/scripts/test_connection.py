import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models import User, Patient, TriagePrediction, DepartmentOccupancy, AuditLog

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"\n✓ Połączenie udane!")
            print(f"  PostgreSQL version: {version[:50]}...")
        
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            patient_count = db.query(Patient).count()
            prediction_count = db.query(TriagePrediction).count()
            occupancy_count = db.query(DepartmentOccupancy).count()
            audit_count = db.query(AuditLog).count()
            
            print(f"  - users: {user_count} rekordów")
            print(f"  - patients: {patient_count} rekordów")
            print(f"  - triage_predictions: {prediction_count} rekordów")
            print(f"  - department_occupancy: {occupancy_count} rekordów")
            print(f"  - audit_log: {audit_count} rekordów")
            
        finally:
            db.close()
        
    except Exception as e:
        print("\nUpewnij się, że:")
        print("  1. Docker container z PostgreSQL jest uruchomiony")
        print("  2. Plik .env zawiera poprawne dane dostępowe")
        print("  3. Baza danych została zainicjalizowana (python scripts/init_db.py)")

if __name__ == "__main__":
    test_connection()
