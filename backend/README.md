# Clinic Triage System - Backend

Backend API dla systemu triaży szpitalnej z integracją ML.

## Setup

1. Utwórz virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows
```

2. Zainstaluj dependencies:
```bash
pip install -r requirements.txt
```

3. Skopiuj .env.example do .env i uzupełnij wartości:
```bash
cp .env.example .env
```

4. Uruchom migracje bazy danych:
```bash
alembic upgrade head
```

5. Uruchom serwer deweloperski:
```bash
uvicorn app.main:app --reload
```

API będzie dostępne pod: http://localhost:8000/docs

## Struktura projektu

```
backend/
├── app/              # Główna aplikacja
│   ├── api/          # Endpointy REST
│   ├── core/         # Konfiguracja, baza, bezpieczeństwo
│   ├── models/       # Modele SQLAlchemy
│   ├── schemas/      # Schematy Pydantic
│   ├── services/     # Logika biznesowa
│   ├── ml/           # Integracja z ML
│   └── utils/        # Funkcje pomocnicze
├── tests/            # Testy jednostkowe
├── scripts/          # Skrypty pomocnicze
└── alembic/          # Migracje bazy danych
```

## Endpointy API

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/auth/login` - Logowanie
- `POST /api/v1/auth/register` - Rejestracja
- `GET /api/v1/patients` - Lista pacjentów
- `POST /api/v1/patients` - Nowy pacjent + predykcja
- `GET /api/v1/triage/stats` - Statystyki triaży
- `GET /api/v1/departments/occupancy` - Obłożenie oddziałów

## Development

```bash
# Uruchom testy
pytest

# Uruchom serwer z auto-reload
uvicorn app.main:app --reload --port 8000

# Utwórz nową migrację
alembic revision --autogenerate -m "Description"

# Zastosuj migracje
alembic upgrade head
```
