"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey,
    Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum

Base = declarative_base()


class UserRole(str, Enum):
    """User role enumeration."""
    MANAGER = "manager"
    AGENT = "agent"
    ADMIN = "admin"


class ValidationSeverityEnum(str, Enum):
    """Validation severity enumeration."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class TaskSeverityEnum(str, Enum):
    """Task severity enumeration."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class TaskStatusEnum(str, Enum):
    """Task status enumeration."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class User(Base):
    """User model for role-based access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.AGENT, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    crm_records = relationship("CRMRecord", back_populates="agent")
    call_records = relationship("CallRecord", back_populates="agent")
    tasks = relationship("OperationalTask", back_populates="assigned_user")
    attendance_logs = relationship("AttendanceLog", back_populates="employee")
    activities = relationship("EmployeeActivity", back_populates="employee")
    scores = relationship("EmployeeScore", back_populates="employee")

    __table_args__ = (
        Index("idx_telegram_id_active", "telegram_id", "is_active"),
        Index("idx_role_active", "role", "is_active"),
    )


class CRMRecord(Base):
    """CRM record model."""
    __tablename__ = "crm_records"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    comment = Column(Text)
    follow_up_date = Column(DateTime, index=True)
    phone_number = Column(String(20), index=True, nullable=False)
    source_file = Column(String(255))
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agent = relationship("User", back_populates="crm_records")
    validation_errors = relationship("ValidationError", back_populates="crm_record")
    appointment = relationship("Appointment", uselist=False, back_populates="crm_record")

    __table_args__ = (
        Index("idx_agent_status", "agent_id", "status"),
        Index("idx_phone_date", "phone_number", "created_at"),
        UniqueConstraint("record_id", name="uq_record_id"),
    )


class ValidationError(Base):
    """Validation error model."""
    __tablename__ = "validation_errors"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("crm_records.id"), nullable=False, index=True)
    rule_name = Column(String(100), nullable=False)
    severity = Column(SQLEnum(ValidationSeverityEnum), nullable=False, index=True)
    description = Column(Text, nullable=False)
    resolved_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    crm_record = relationship("CRMRecord", back_populates="validation_errors")

    __table_args__ = (
        Index("idx_severity_resolved", "severity", "resolved_at"),
    )


class Appointment(Base):
    """Appointment model."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String(100), unique=True, index=True, nullable=False)
    client_phone = Column(String(20), index=True, nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING")  # CALLED, MISSED, HIDDEN
    matched_call_id = Column(Integer, ForeignKey("call_records.id"))
    record_id = Column(Integer, ForeignKey("crm_records.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    call_record = relationship("CallRecord", back_populates="appointments")
    crm_record = relationship("CRMRecord", back_populates="appointment")

    __table_args__ = (
        Index("idx_phone_scheduled", "client_phone", "scheduled_at"),
        Index("idx_status_scheduled", "status", "scheduled_at"),
    )


class CallRecord(Base):
    """Call record model."""
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    client_phone = Column(String(20), index=True, nullable=False)
    called_at = Column(DateTime, nullable=False, index=True)
    duration_seconds = Column(Integer)
    outcome = Column(String(50), nullable=False)  # answered, no_answer, voicemail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agent = relationship("User", back_populates="call_records")
    appointments = relationship("Appointment", back_populates="call_record")

    __table_args__ = (
        Index("idx_agent_called_at", "agent_id", "called_at"),
        Index("idx_phone_outcome", "client_phone", "outcome"),
    )


class EmployeeActivity(Base):
    """Employee activity tracking model."""
    __tablename__ = "employee_activities"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)  # login, call, crm_update, telegram_msg
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("User", back_populates="activities")

    __table_args__ = (
        Index("idx_employee_timestamp", "employee_id", "timestamp"),
        Index("idx_activity_type_time", "activity_type", "timestamp"),
    )


class EmployeeScore(Base):
    """Employee performance and risk score model."""
    __tablename__ = "employee_scores"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    risk_score = Column(Float, default=50.0)  # 0-100, higher = riskier
    performance_score = Column(Float, default=50.0)  # 0-100, higher = better
    flags = Column(Text)  # JSON-encoded list of flags
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("User", back_populates="scores")

    __table_args__ = (
        Index("idx_employee_date", "employee_id", "date"),
        UniqueConstraint("employee_id", "date", name="uq_employee_daily_score"),
    )


class OperationalTask(Base):
    """Operational task model."""
    __tablename__ = "operational_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    issue_type = Column(String(100), nullable=False)  # validation_error, missed_appointment, etc
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(TaskSeverityEnum), nullable=False, index=True)
    deadline = Column(DateTime, nullable=False, index=True)
    status = Column(SQLEnum(TaskStatusEnum), default=TaskStatusEnum.OPEN, index=True)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    assigned_user = relationship("User", back_populates="tasks")

    __table_args__ = (
        Index("idx_assigned_status", "assigned_to", "status"),
        Index("idx_severity_deadline", "severity", "deadline"),
    )


class AttendanceLog(Base):
    """Employee attendance log model."""
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    login_at = Column(DateTime, nullable=False, index=True)
    logout_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employee = relationship("User", back_populates="attendance_logs")

    __table_args__ = (
        Index("idx_employee_login", "employee_id", "login_at"),
    )


class ExecutiveSummary(Base):
    """Daily executive summary model."""
    __tablename__ = "executive_summaries"

    id = Column(Integer, primary_key=True, index=True)
    summary_date = Column(DateTime, nullable=False, unique=True, index=True)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditLog(Base):
    """Audit log for compliance and monitoring."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(255), nullable=False)
    endpoint = Column(String(255))
    request_data = Column(Text)  # JSON-encoded request body
    response_status = Column(Integer)
    ip_address = Column(String(45))  # IPv4 + IPv6 support
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_user_action_time", "user_id", "action", "created_at"),
    )
