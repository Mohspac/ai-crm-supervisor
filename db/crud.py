"""CRUD operations for database models."""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db import models, schemas
from loguru import logger


# ============================================================================
# User CRUD
# ============================================================================

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> models.User:
    """Create a new user."""
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"Created user: {db_user.telegram_id}")
    return db_user


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[models.User]:
    """Get user by Telegram ID."""
    result = await db.execute(
        select(models.User).where(models.User.telegram_id == telegram_id)
    )
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """Get user by ID."""
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalars().first()


async def get_users_by_role(db: AsyncSession, role: models.UserRole) -> List[models.User]:
    """Get all users with a specific role."""
    result = await db.execute(
        select(models.User).where(
            and_(models.User.role == role, models.User.is_active == True)
        )
    )
    return result.scalars().all()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get all users with pagination."""
    result = await db.execute(
        select(models.User).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def update_user(
    db: AsyncSession, user_id: int, user_update: schemas.UserUpdate
) -> Optional[models.User]:
    """Update user information."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"Updated user: {user_id}")
    return db_user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Soft delete user (mark inactive)."""
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False
    
    db_user.is_active = False
    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    await db.commit()
    logger.info(f"Deleted user: {user_id}")
    return True


# ============================================================================
# CRM Record CRUD
# ============================================================================

async def create_crm_record(db: AsyncSession, record: schemas.CRMRecordCreate) -> models.CRMRecord:
    """Create a new CRM record."""
    db_record = models.CRMRecord(**record.model_dump())
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)
    logger.info(f"Created CRM record: {db_record.record_id}")
    return db_record


async def get_crm_record_by_id(db: AsyncSession, record_id: int) -> Optional[models.CRMRecord]:
    """Get CRM record by ID."""
    result = await db.execute(
        select(models.CRMRecord).where(models.CRMRecord.id == record_id)
    )
    return result.scalars().first()


async def get_crm_record_by_record_id(db: AsyncSession, record_id: str) -> Optional[models.CRMRecord]:
    """Get CRM record by record_id."""
    result = await db.execute(
        select(models.CRMRecord).where(models.CRMRecord.record_id == record_id)
    )
    return result.scalars().first()


async def get_crm_records_by_agent(
    db: AsyncSession, agent_id: int, skip: int = 0, limit: int = 100
) -> List[models.CRMRecord]:
    """Get all CRM records for an agent."""
    result = await db.execute(
        select(models.CRMRecord)
        .where(models.CRMRecord.agent_id == agent_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_crm_records_by_status(
    db: AsyncSession, status: str, skip: int = 0, limit: int = 100
) -> List[models.CRMRecord]:
    """Get CRM records by status."""
    result = await db.execute(
        select(models.CRMRecord)
        .where(models.CRMRecord.status == status)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_inactive_crm_records(
    db: AsyncSession, days: int = 14
) -> List[models.CRMRecord]:
    """Get CRM records not updated for X days."""
    threshold_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(models.CRMRecord).where(
            models.CRMRecord.last_updated < threshold_date
        )
    )
    return result.scalars().all()


async def update_crm_record(
    db: AsyncSession, record_id: int, data: dict
) -> Optional[models.CRMRecord]:
    """Update CRM record."""
    db_record = await get_crm_record_by_id(db, record_id)
    if not db_record:
        return None
    
    for field, value in data.items():
        if hasattr(db_record, field):
            setattr(db_record, field, value)
    
    db_record.last_updated = datetime.utcnow()
    db.add(db_record)
    await db.commit()
    await db.refresh(db_record)
    return db_record


async def batch_create_crm_records(
    db: AsyncSession, records: List[schemas.CRMRecordCreate]
) -> int:
    """Batch create CRM records."""
    db_records = [models.CRMRecord(**record.model_dump()) for record in records]
    db.add_all(db_records)
    await db.commit()
    logger.info(f"Batch created {len(db_records)} CRM records")
    return len(db_records)


# ============================================================================
# Validation Error CRUD
# ============================================================================

async def create_validation_error(
    db: AsyncSession, error: schemas.ValidationErrorCreate
) -> models.ValidationError:
    """Create validation error."""
    db_error = models.ValidationError(**error.model_dump())
    db.add(db_error)
    await db.commit()
    await db.refresh(db_error)
    return db_error


async def get_validation_errors_by_record(
    db: AsyncSession, record_id: int
) -> List[models.ValidationError]:
    """Get all validation errors for a record."""
    result = await db.execute(
        select(models.ValidationError).where(
            models.ValidationError.record_id == record_id
        )
    )
    return result.scalars().all()


async def get_unresolved_validation_errors(
    db: AsyncSession, severity: Optional[models.ValidationSeverityEnum] = None
) -> List[models.ValidationError]:
    """Get unresolved validation errors."""
    query = select(models.ValidationError).where(
        models.ValidationError.resolved_at == None
    )
    
    if severity:
        query = query.where(models.ValidationError.severity == severity)
    
    result = await db.execute(query)
    return result.scalars().all()


async def resolve_validation_error(
    db: AsyncSession, error_id: int
) -> Optional[models.ValidationError]:
    """Mark validation error as resolved."""
    db_error = await db.get(models.ValidationError, error_id)
    if not db_error:
        return None
    
    db_error.resolved_at = datetime.utcnow()
    db.add(db_error)
    await db.commit()
    await db.refresh(db_error)
    return db_error


async def batch_create_validation_errors(
    db: AsyncSession, errors: List[schemas.ValidationErrorCreate]
) -> int:
    """Batch create validation errors."""
    db_errors = [models.ValidationError(**error.model_dump()) for error in errors]
    db.add_all(db_errors)
    await db.commit()
    logger.info(f"Created {len(db_errors)} validation errors")
    return len(db_errors)


# ============================================================================
# Appointment CRUD
# ============================================================================

async def create_appointment(
    db: AsyncSession, appointment: schemas.AppointmentCreate
) -> models.Appointment:
    """Create appointment."""
    db_appointment = models.Appointment(**appointment.model_dump())
    db.add(db_appointment)
    await db.commit()
    await db.refresh(db_appointment)
    return db_appointment


async def get_appointment_by_id(
    db: AsyncSession, appointment_id: int
) -> Optional[models.Appointment]:
    """Get appointment by ID."""
    result = await db.execute(
        select(models.Appointment).where(models.Appointment.id == appointment_id)
    )
    return result.scalars().first()


async def get_unmatched_appointments(db: AsyncSession) -> List[models.Appointment]:
    """Get appointments without matched calls."""
    result = await db.execute(
        select(models.Appointment).where(
            models.Appointment.matched_call_id == None
        )
    )
    return result.scalars().all()


async def update_appointment_status(
    db: AsyncSession, appointment_id: int, status: str, call_id: Optional[int] = None
) -> Optional[models.Appointment]:
    """Update appointment status."""
    db_apt = await get_appointment_by_id(db, appointment_id)
    if not db_apt:
        return None
    
    db_apt.status = status
    if call_id:
        db_apt.matched_call_id = call_id
    
    db.add(db_apt)
    await db.commit()
    await db.refresh(db_apt)
    return db_apt


async def batch_create_appointments(
    db: AsyncSession, appointments: List[schemas.AppointmentCreate]
) -> int:
    """Batch create appointments."""
    db_apts = [models.Appointment(**apt.model_dump()) for apt in appointments]
    db.add_all(db_apts)
    await db.commit()
    logger.info(f"Created {len(db_apts)} appointments")
    return len(db_apts)


# ============================================================================
# Call Record CRUD
# ============================================================================

async def create_call_record(
    db: AsyncSession, call: schemas.CallRecordCreate
) -> models.CallRecord:
    """Create call record."""
    db_call = models.CallRecord(**call.model_dump())
    db.add(db_call)
    await db.commit()
    await db.refresh(db_call)
    return db_call


async def get_call_record_by_id(db: AsyncSession, call_id: int) -> Optional[models.CallRecord]:
    """Get call record by ID."""
    result = await db.execute(
        select(models.CallRecord).where(models.CallRecord.id == call_id)
    )
    return result.scalars().first()


async def get_calls_by_agent_and_date(
    db: AsyncSession, agent_id: int, date: datetime
) -> List[models.CallRecord]:
    """Get calls for agent on specific date."""
    start = date.replace(hour=0, minute=0, second=0)
    end = start + timedelta(days=1)
    
    result = await db.execute(
        select(models.CallRecord).where(
            and_(
                models.CallRecord.agent_id == agent_id,
                models.CallRecord.called_at >= start,
                models.CallRecord.called_at < end,
            )
        )
    )
    return result.scalars().all()


async def get_calls_by_phone_and_date_range(
    db: AsyncSession, phone: str, start_date: datetime, end_date: datetime
) -> List[models.CallRecord]:
    """Get calls by phone number within date range."""
    result = await db.execute(
        select(models.CallRecord).where(
            and_(
                models.CallRecord.client_phone == phone,
                models.CallRecord.called_at >= start_date,
                models.CallRecord.called_at <= end_date,
            )
        )
    )
    return result.scalars().all()


async def batch_create_call_records(
    db: AsyncSession, calls: List[schemas.CallRecordCreate]
) -> int:
    """Batch create call records."""
    db_calls = [models.CallRecord(**call.model_dump()) for call in calls]
    db.add_all(db_calls)
    await db.commit()
    logger.info(f"Created {len(db_calls)} call records")
    return len(db_calls)


# ============================================================================
# Employee Activity CRUD
# ============================================================================

async def create_employee_activity(
    db: AsyncSession, activity: schemas.EmployeeActivityCreate
) -> models.EmployeeActivity:
    """Create employee activity."""
    db_activity = models.EmployeeActivity(**activity.model_dump())
    db.add(db_activity)
    await db.commit()
    await db.refresh(db_activity)
    return db_activity


async def get_employee_activities_by_date(
    db: AsyncSession, employee_id: int, date: datetime
) -> List[models.EmployeeActivity]:
    """Get employee activities for a specific date."""
    start = date.replace(hour=0, minute=0, second=0)
    end = start + timedelta(days=1)
    
    result = await db.execute(
        select(models.EmployeeActivity).where(
            and_(
                models.EmployeeActivity.employee_id == employee_id,
                models.EmployeeActivity.timestamp >= start,
                models.EmployeeActivity.timestamp < end,
            )
        ).order_by(models.EmployeeActivity.timestamp)
    )
    return result.scalars().all()


async def get_employee_activities_by_type(
    db: AsyncSession, employee_id: int, activity_type: str, hours: int = 24
) -> List[models.EmployeeActivity]:
    """Get employee activities of specific type in last N hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(models.EmployeeActivity).where(
            and_(
                models.EmployeeActivity.employee_id == employee_id,
                models.EmployeeActivity.activity_type == activity_type,
                models.EmployeeActivity.timestamp >= cutoff,
            )
        ).order_by(desc(models.EmployeeActivity.timestamp))
    )
    return result.scalars().all()


async def batch_create_employee_activities(
    db: AsyncSession, activities: List[schemas.EmployeeActivityCreate]
) -> int:
    \"\"\"Batch create employee activities.\"\"\"
    db_activities = [models.EmployeeActivity(**act.model_dump()) for act in activities]
    db.add_all(db_activities)
    await db.commit()
    return len(db_activities)


# ============================================================================
# Employee Score CRUD
# ============================================================================

async def create_employee_score(
    db: AsyncSession, score: schemas.EmployeeScoreBase
) -> models.EmployeeScore:
    """Create employee score."""
    db_score = models.EmployeeScore(**score.model_dump())
    db.add(db_score)
    await db.commit()
    await db.refresh(db_score)
    return db_score


async def get_employee_score_by_date(
    db: AsyncSession, employee_id: int, date: datetime
) -> Optional[models.EmployeeScore]:
    """Get employee score for specific date."""
    result = await db.execute(
        select(models.EmployeeScore).where(
            and_(
                models.EmployeeScore.employee_id == employee_id,
                func.date(models.EmployeeScore.date) == date.date(),
            )
        )
    )
    return result.scalars().first()


async def get_employee_scores_by_date_range(
    db: AsyncSession, employee_id: int, start_date: datetime, end_date: datetime
) -> List[models.EmployeeScore]:
    """Get employee scores within date range."""
    result = await db.execute(
        select(models.EmployeeScore).where(
            and_(
                models.EmployeeScore.employee_id == employee_id,
                models.EmployeeScore.date >= start_date,
                models.EmployeeScore.date <= end_date,
            )
        ).order_by(desc(models.EmployeeScore.date))
    )
    return result.scalars().all()


# ============================================================================
# Operational Task CRUD
# ============================================================================

async def create_operational_task(
    db: AsyncSession, task: schemas.OperationalTaskCreate
) -> models.OperationalTask:
    """Create operational task."""
    db_task = models.OperationalTask(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    logger.info(f"Created task: {db_task.task_id}")
    return db_task


async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[models.OperationalTask]:
    """Get task by ID."""
    result = await db.execute(
        select(models.OperationalTask).where(models.OperationalTask.id == task_id)
    )
    return result.scalars().first()


async def get_tasks_assigned_to_user(
    db: AsyncSession, user_id: int, status: Optional[models.TaskStatusEnum] = None
) -> List[models.OperationalTask]:
    """Get tasks assigned to user."""
    query = select(models.OperationalTask).where(
        models.OperationalTask.assigned_to == user_id
    )
    
    if status:
        query = query.where(models.OperationalTask.status == status)
    
    result = await db.execute(query.order_by(models.OperationalTask.deadline))
    return result.scalars().all()


async def get_overdue_critical_tasks(db: AsyncSession) -> List[models.OperationalTask]:
    """Get critical tasks past deadline."""
    result = await db.execute(
        select(models.OperationalTask).where(
            and_(
                models.OperationalTask.severity == models.TaskSeverityEnum.CRITICAL,
                models.OperationalTask.status != models.TaskStatusEnum.RESOLVED,
                models.OperationalTask.deadline < datetime.utcnow(),
            )
        )
    )
    return result.scalars().all()


async def update_task_status(
    db: AsyncSession, task_id: int, status: models.TaskStatusEnum
) -> Optional[models.OperationalTask]:
    """Update task status."""
    db_task = await get_task_by_id(db, task_id)
    if not db_task:
        return None
    
    db_task.status = status
    if status == models.TaskStatusEnum.RESOLVED:
        db_task.resolved_at = datetime.utcnow()
    
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    logger.info(f"Updated task status: {task_id} -> {status}")
    return db_task


async def batch_create_tasks(
    db: AsyncSession, tasks: List[schemas.OperationalTaskCreate]
) -> int:
    """Batch create tasks."""
    db_tasks = [models.OperationalTask(**task.model_dump()) for task in tasks]
    db.add_all(db_tasks)
    await db.commit()
    logger.info(f"Created {len(db_tasks)} tasks")
    return len(db_tasks)


# ============================================================================
# Attendance Log CRUD
# ============================================================================

async def create_attendance_log(
    db: AsyncSession, employee_id: int, login_at: datetime
) -> models.AttendanceLog:
    """Create attendance log entry."""
    db_log = models.AttendanceLog(employee_id=employee_id, login_at=login_at)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def update_attendance_logout(
    db: AsyncSession, log_id: int, logout_at: datetime
) -> Optional[models.AttendanceLog]:
    """Update logout time."""
    db_log = await db.get(models.AttendanceLog, log_id)
    if not db_log:
        return None
    
    db_log.logout_at = logout_at
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


# ============================================================================
# Executive Summary CRUD
# ============================================================================

async def create_executive_summary(
    db: AsyncSession, summary_date: datetime, content: str
) -> models.ExecutiveSummary:
    """Create executive summary."""
    db_summary = models.ExecutiveSummary(
        summary_date=summary_date,
        content=content,
        sent_at=datetime.utcnow()
    )
    db.add(db_summary)
    await db.commit()
    await db.refresh(db_summary)
    logger.info(f"Created executive summary for {summary_date.date()}")
    return db_summary


async def get_executive_summary_by_date(
    db: AsyncSession, date: datetime
) -> Optional[models.ExecutiveSummary]:
    """Get executive summary for date."""
    result = await db.execute(
        select(models.ExecutiveSummary).where(
            func.date(models.ExecutiveSummary.summary_date) == date.date()
        )
    )
    return result.scalars().first()


# ============================================================================
# Audit Log CRUD
# ============================================================================

async def create_audit_log(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    endpoint: Optional[str] = None,
    request_data: Optional[str] = None,
    response_status: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> models.AuditLog:
    \"\"\"Create audit log entry.\"\"\"
    db_log = models.AuditLog(
        user_id=user_id,
        action=action,
        endpoint=endpoint,
        request_data=request_data,
        response_status=response_status,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log
