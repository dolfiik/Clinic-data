from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.get("/me")
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
):
    """Pobiera informacje o zalogowanym użytkowniku"""
    # TODO: Implementacja
    return {"message": "Informacje o użytkowniku - TODO"}
