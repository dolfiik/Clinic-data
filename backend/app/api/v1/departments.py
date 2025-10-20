from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.get("/occupancy")
async def get_current_occupancy(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pobiera aktualne obłożenie oddziałów"""
    # TODO: Implementacja
    return {"message": "Obłożenie oddziałów - TODO"}
