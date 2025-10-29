from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse, UserInDB
from app.schemas.common import PaginatedResponse, MessageResponse
from app.schemas.patient import (
    PatientBase,
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListItem,
    PatientWithPrediction,
    PatientWithDetails
)
from app.schemas.triage import (
    TriagePredictionBase,
    TriagePredictionCreate,
    TriagePredictionResponse,
    TriagePredictRequest,
    TriagePredictResponse,
    TriageStatsResponse,
    DailyTriageStats,
    CategoryDistribution,
    TriageAnalytics,
    TriagePreviewRequest,
    TriagePreviewResponse,
    TriageConfirmRequest,
    TriageConfirmResponse
)
from app.schemas.department import (
    DepartmentOccupancyBase,
    DepartmentOccupancyCreate,
    DepartmentOccupancyResponse,
    DepartmentInfo,
    CurrentOccupancyResponse,
    DepartmentCapacity,
    OccupancyHistory,
    DepartmentStats
)
from app.schemas.audit import (
    AuditLogBase,
    AuditLogCreate,
    AuditLogResponse,
    AuditLogWithUser,
    AuditLogFilter
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    # Common
    "PaginatedResponse",
    "MessageResponse",
    # Patient
    "PatientBase",
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "PatientListItem",
    "PatientWithPrediction",
    "PatientWithDetails",
    # Triage
    "TriagePredictionBase",
    "TriagePredictionCreate",
    "TriagePredictionResponse",
    "TriagePredictRequest",
    "TriagePredictResponse",
    "TriageStatsResponse",
    "DailyTriageStats",
    "CategoryDistribution",
    "TriageAnalytics",
    "TriagePreviewRequest",
    "TriagePreviewResponse",
    "TriageConfirmRequest",
    "TriageConfirmResponse",
    # Department
    "DepartmentOccupancyBase",
    "DepartmentOccupancyCreate",
    "DepartmentOccupancyResponse",
    "DepartmentInfo",
    "CurrentOccupancyResponse",
    "DepartmentCapacity",
    "OccupancyHistory",
    "DepartmentStats",
    # Audit
    "AuditLogBase",
    "AuditLogCreate",
    "AuditLogResponse",
    "AuditLogWithUser",
    "AuditLogFilter",
]
