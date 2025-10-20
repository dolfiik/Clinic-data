from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, patients, triage, departments, users

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Zmień na konkretne domeny w production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includy routerów
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(patients.router, prefix=f"{settings.API_V1_PREFIX}/patients", tags=["Patients"])
app.include_router(triage.router, prefix=f"{settings.API_V1_PREFIX}/triage", tags=["Triage"])
app.include_router(departments.router, prefix=f"{settings.API_V1_PREFIX}/departments", tags=["Departments"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])

@app.get("/")
async def root():
    return {
        "message": "Clinic Triage System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
