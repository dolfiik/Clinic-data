from app.core.database import engine, Base
from app.models import User, Patient, TriagePrediction, DepartmentOccupancy, AuditLog

def init_db():
    print("Tworzenie tabel w bazie danych...")
    Base.metadata.create_all(bind=engine)
    print(" Baza danych zainicjalizowana")

if __name__ == "__main__":
    init_db()
