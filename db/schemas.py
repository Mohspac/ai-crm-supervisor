"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    """User role."""
    MANAGER = "manager"
    AGENT = "agent"
    ADMIN = "admin"


class ValidationSeverity(str, Enum):
    """Validation severity."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class TaskSeverity(str, Enum):
    """Task severity."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class TaskStatus(str, Enum):
    """Task status."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    telegram_id: int
    name: str
    role: UserRole = UserRole.AGENT


class UserCreate(UserBase):
    """User creation schema."""
    pass


class UserUpdate(BaseModel):
    """User update schema."""
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# CRM Record Schemas
class CRMRecordBase(BaseModel):
    """Base CRM record schema."""
    record_id: str
    agent_id: int
    status: str
    comment: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    phone_number: str


class CRMRecordCreate(CRMRecordBase):
    """CRM record creation schema."""
    source_file: Optional[str] = None


class CRMRecordResponse(CRMRecordBase):
    """CRM record response schema."""
    id: int
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Validation Error Schemas
class ValidationErrorBase(BaseModel):
    """Base validation error schema."""
    rule_name: str
    severity: ValidationSeverity
    description: str


class ValidationErrorCreate(ValidationErrorBase):
    """Validation error creation schema."""
    record_id: int


class ValidationErrorResponse(ValidationErrorBase):
    """Validation error response schema."""
    id: int
    record_id: int
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationReport(BaseModel):
    """Validation report schema."""
    total_records: int
    total_errors: int
    critical_errors: int
    warning_errors: int
    info_errors: int
    errors: List[ValidationErrorResponse] = []


# Appointment Schemas
class AppointmentBase(BaseModel):
    """Base appointment schema."""
    appointment_id: str
    client_phone: str
    assigned_agent_id: Optional[int] = None
    scheduled_at: datetime


class AppointmentCreate(AppointmentBase):
    """Appointment creation schema."""
    pass


class AppointmentResponse(AppointmentBase):
    """Appointment response schema."""
    id: int
    status: Optional[str] = None
    matched_call_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Call Record Schemas
class CallRecordBase(BaseModel):
    """Base call record schema."""
    call_id: str
    agent_id: int
    client_phone: str
    called_at: datetime
    outcome: Optional[str] = None


class CallRecordCreate(CallRecordBase):
    """Call record creation schema."""
    duration_seconds: Optional[int] = None


class CallRecordResponse(CallRecordBase):
    """Call record response schema."""
    id: int
    duration_seconds: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Employee Activity Schemas
class EmployeeActivityBase(BaseModel):
    """Base employee activity schema."""
    employee_id: int
    timestamp: datetime
    activity_type: str
    details: Optional[str] = None


class EmployeeActivityCreate(EmployeeActivityBase):
    """Employee activity creation schema."""
    pass


class EmployeeActivityResponse(EmployeeActivityBase):
    """Employee activity response schema."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Employee Score Schemas
class EmployeeScoreBase(BaseModel):
    """Base employee score schema."""
    employee_id: int
    date: datetime
    risk_score: float = Field(ge=0, le=100)
    performance_score: float = Field(ge=0, le=100)
    flags: Optional[str] = None


class EmployeeScoreResponse(EmployeeScoreBase):
    """Employee score response schema."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Operational Task Schemas
class OperationalTaskBase(BaseModel):
    """Base operational task schema."""
    task_id: str
    assigned_to: int
    issue_type: str
    description: str
    severity: TaskSeverity
    deadline: datetime


class OperationalTaskCreate(OperationalTaskBase):
    """Operational task creation schema."""
    pass


class OperationalTaskUpdate(BaseModel):
    """Operational task update schema."""
    description: Optional[str] = None
    severity: Optional[TaskSeverity] = None
    deadline: Optional[datetime] = None
    status: Optional[TaskStatus] = None


class OperationalTaskResponse(OperationalTaskBase):
    """Operational task response schema."""
    id: int
    status: TaskStatus
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Report Request Schemas
class ReportRequestCreate(BaseModel):
    """Report request creation schema."""
    staff_id: int
    report_type: str  # "daily", "weekly", "monthly"
    requested_by: int


class ReportRequestResponse(BaseModel):
    """Report request response schema."""
    id: int
    staff_id: int
    report_type: str
    requested_by: int
    status: str
    created_at: datetime
    updated_at: datetime


# AI Status Advisor Schemas
class StatusAdviceRequest(BaseModel):
    """AI status advice request schema."""
    situation_description: str = Field(..., min_length=10, max_length=1000)
    customer_phone: Optional[str] = None
    current_status: Optional[str] = None


class StatusAdviceResponse(BaseModel):
    """AI status advice response schema."""
    recommended_status: str
    crm_comment: str
    suggested_follow_up: str
    follow_up_days: int
    priority_level: str  # High, Medium, Low
    confidence_score: float = Field(ge=0, le=1)


# Reconciliation Report Schemas
class AppointmentReconciliationReport(BaseModel):
    """Appointment reconciliation report schema."""
    total_appointments: int
    called: int
    missed: int
    hidden: int
    matched_calls: int
    unmatched_appointments: List[AppointmentResponse] = []


# Executive Summary Schema
class ExecutiveSummaryResponse(BaseModel):
    """Executive summary response schema."""
    summary_date: datetime
    content: str
    reports_processed: int
    crm_errors_detected: int
    missed_appointments: int
    open_critical_tasks: int
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Batch Operation Schemas
class BatchUploadResponse(BaseModel):
    """Batch upload response schema."""
    total_records: int
    successful: int
    failed: int
    errors: List[str] = []


class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    services: dict
