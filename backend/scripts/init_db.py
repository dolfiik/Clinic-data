import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models import User, Patient, TriagePrediction, DepartmentOccupancy, AuditLog

def init_db():
    print("\nTworzenie tabel...")
    Base.metadata.create_all(bind=engine)
    
    print("Tabele utworzone:")
    print(" - users")
    print(" - patients")
    print(" - triage_predictions")
    print(" - department_occupancy")
    print(" - audit_log")

if __name__ == "__main__":
    init_db()
