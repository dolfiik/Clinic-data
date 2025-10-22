from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, patients, triage, departments, users, audit

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    System wspierający proces triaży szpitalnej z integracją Machine Learning.
    
    ### Główne funkcje:
    
    * **Autentykacja** - Rejestracja, logowanie, zarządzanie tokenami JWT
    * **Pacjenci** - Pełny CRUD, wyszukiwanie, statusy
    * **Triąż** - Predykcje ML (Random Forest), statystyki, analityka
    * **Oddziały** - Monitorowanie obłożenia, historia, prognozy
    * **Użytkownicy** - Zarządzanie kontami, role, uprawnienia
    * **Audit Log** - Pełna historia akcji, filtry, timeline
    
    ### Autoryzacja:
    
    Większość endpointów wymaga Bearer Token w nagłówku Authorization:
    ```
    Authorization: Bearer <your_access_token>
    ```
    
    Token otrzymujesz po zalogowaniu przez `POST /api/v1/auth/login`
    
    ### Role użytkowników:
    
    * **admin** - Pełny dostęp do wszystkich funkcji
    * **doctor** - Dostęp do pacjentów, triaży, statystyk
    * **nurse** - Dostęp do pacjentów, triaży, obłożenia
    * **receptionist** - Ograniczony dostęp (przeglądanie)
    
    ### Model ML:
    
    System używa Random Forest Classifier do predykcji kategorii triaży (1-5):
    * **Kategoria 1** - Natychmiastowy (resuscytacja)
    * **Kategoria 2** - Pilny (ciężki stan)
    * **Kategoria 3** - Stabilny
    * **Kategoria 4** - Niski priorytet
    * **Kategoria 5** - Bardzo niski
    
    Model trenowany na 20 000 przypadków medycznych z accuracy ~95%.
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Clinic Triage System",
        "email": "support@clinic-triage.example.com"
    },
    license_info={
        "name": "MIT",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"],
    responses={401: {"description": "Unauthorized"}}
)

app.include_router(
    patients.router,
    prefix=f"{settings.API_V1_PREFIX}/patients",
    tags=["Patients"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Patient not found"}
    }
)

app.include_router(
    triage.router,
    prefix=f"{settings.API_V1_PREFIX}/triage",
    tags=["Triage & ML"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Not found"},
        503: {"description": "Model not available"}
    }
)

app.include_router(
    departments.router,
    prefix=f"{settings.API_V1_PREFIX}/departments",
    tags=["Departments"],
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Bad request"}
    }
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "User not found"}
    }
)

app.include_router(
    audit.router,
    prefix=f"{settings.API_V1_PREFIX}/audit",
    tags=["Audit Log"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - informacje o API
    
    **Zwraca:**
    - Nazwę i wersję API
    - Link do dokumentacji
    - Status systemu
    """
    return {
        "message": "Clinic Triage System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "operational",
        "features": {
            "authentication": True,
            "ml_predictions": True,
            "department_monitoring": True,
            "audit_logging": True
        }
    }

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint - sprawdza stan systemu
    
    **Zwraca:**
    - Status: healthy/degraded/down
    - Informacje o komponentach
    """
    from app.ml.predictor import predictor
    model_status = "healthy" if predictor.model is not None else "degraded"
    
    from app.core.database import engine
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        database_status = "down"
    
    overall_status = "healthy" if (model_status == "healthy" and database_status == "healthy") else "degraded"
    
    return {
        "status": overall_status,
        "components": {
            "api": "healthy",
            "database": database_status,
            "ml_model": model_status
        },
        "timestamp": "2025-10-22T15:30:00Z"
    }

@app.get("/version", tags=["System"])
async def get_version():
    """
    Pobiera informacje o wersji systemu
    
    **Zwraca:**
    - Wersja API
    - Wersja modelu ML
    - Informacje o buildzie
    """
    from app.ml.predictor import predictor
    
    return {
        "api_version": "1.0.0",
        "model_version": predictor.model_version if predictor.model else "not loaded",
        "build_date": "2025-10-22",
        "environment": "development"  
    }

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handler dla błędów 404"""
    return {
        "error": "Not Found",
        "detail": "The requested resource was not found",
        "path": str(request.url)
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handler dla błędów 500"""
    return {
        "error": "Internal Server Error",
        "detail": "An unexpected error occurred. Please contact support.",
        "path": str(request.url)
    }

@app.on_event("startup")
async def startup_event():
    
    from app.ml.predictor import predictor
    if predictor.model:
        print(f"ML Model loaded: {predictor.model_version}")
    else:
        print(" ML Model not loaded - predictions will not be available")
    
    from app.core.database import engine
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        print("Database connection: OK")
    except Exception as e:
        print(f"Database connection: FAILED - {e}")
    
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"ReDoc: http://localhost:8000/redoc")

@app.on_event("shutdown")
async def shutdown_event():
    print("Clinic Triage System API - SHUTTING DOWN")
