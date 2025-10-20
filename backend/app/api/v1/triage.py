from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.get("/stats")
async def get_triage_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Pobiera statystyki triaży"""
    # TODO: Implementacja
    return {"message": "Statystyki triaży - TODO"}
