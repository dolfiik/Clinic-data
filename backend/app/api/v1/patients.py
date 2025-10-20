from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.get("/")
async def get_patients(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pobiera listę pacjentów"""
    # TODO: Implementacja
    return {"message": "Lista pacjentów - TODO"}

@router.post("/")
async def create_patient(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Tworzy nowego pacjenta i wykonuje predykcję triaży"""
    # TODO: Implementacja
    return {"message": "Utworzono pacjenta - TODO"}

@router.get("/{patient_id}")
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pobiera dane pacjenta"""
    # TODO: Implementacja
    return {"message": f"Pacjent {patient_id} - TODO"}
