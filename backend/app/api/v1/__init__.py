"""
API v1 Routers

Eksportuje wszystkie routery dla wersji 1 API.
"""

from app.api.v1 import auth, patients, triage, departments, users, audit

__all__ = [
    "auth",
    "patients",
    "triage",
    "departments",
    "users",
    "audit"
]
