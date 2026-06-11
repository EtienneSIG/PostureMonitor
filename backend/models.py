"""
Database models for Posture Monitor Pro.

Aligned with compliance requirements:
- User consent tracking (EU-02, EU-05)
- Data retention and deletion (EU-03, EU-04)
- Audit logging (EU-06, NA-06)
- DSAR tracking (EU-04, NA-02)
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


# ============================================================================
# DATABASE MODELS (SQL Alchemy)
# ============================================================================

class User(Base):
    """User account with compliance metadata."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=True, index=True)  # Optional for local use
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete for audit trail
    
    # Consent & Legal (EU-02, EU-05, NA-03)
    consent_version = Column(String, nullable=False, default="1.0")
    consent_given_at = Column(DateTime, nullable=True)
    consent_withdrawn_at = Column(DateTime, nullable=True)
    
    # Age gate (COPPA - NA-04)
    date_of_birth = Column(DateTime, nullable=True)  # Hash this in production
    parental_consent_given = Column(Boolean, default=False)
    
    # Regional preferences (for legal compliance)
    region = Column(String, default="EU")  # EU, US, CA, MX
    
    # Data processing preferences
    analytics_enabled = Column(Boolean, default=False)  # Separate consent
    share_improvement_data = Column(Boolean, default=False)


class ConsentLog(Base):
    """Audit log for consent changes (EU-02, EU-05)."""
    
    __tablename__ = "consent_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action = Column(String, nullable=False)  # "given", "withdrawn", "updated"
    consent_type = Column(String, nullable=False)  # "posture_tracking", "analytics", etc.
    version = Column(String, nullable=False)  # Consent version
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Auto-delete after log retention period (EU-03)
    delete_at = Column(DateTime, nullable=True)  # Scheduled deletion


class PostureData(Base):
    """Posture analysis results (EU-01, EU-03)."""
    
    __tablename__ = "posture_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Posture metrics (aggregated only, never raw frames)
    spine_angle = Column(Float, nullable=True)
    shoulder_symmetry = Column(Float, nullable=True)  # 0-100%
    neck_angle = Column(Float, nullable=True)
    alert_triggered = Column(Boolean, default=False)
    alert_level = Column(String, nullable=True)  # "info", "warning", "critical"
    
    # Metadata
    session_id = Column(String, nullable=True, index=True)
    processing_model = Column(String, default="mediapipe-pose-v1")  # AI transparency (EU-06)
    
    # Auto-delete after retention period (EU-03)
    delete_at = Column(DateTime, nullable=True, index=True)  # TTL for cleanup


class AuditLog(Base):
    """Comprehensive audit log for compliance (EU-06, NA-06)."""
    
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    
    # Event type
    event_type = Column(String, nullable=False, index=True)  # "login", "dsar_request", "data_access", "export", "delete", etc.
    action = Column(String, nullable=False)
    resource = Column(String, nullable=True)  # What resource was accessed
    
    # Details (JSON for flexibility)
    details = Column(JSON, nullable=True)
    status = Column(String, nullable=True)  # "success", "failed"
    error_message = Column(String, nullable=True)
    
    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Never auto-delete (legal requirement 1 year - EU-03, NA-02)
    delete_at = Column(DateTime, nullable=True)


class DSARRequest(Base):
    """Data Subject Access Request tracking (EU-04, NA-02)."""
    
    __tablename__ = "dsar_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    request_type = Column(String, nullable=False)  # "access", "delete", "export", "correct"
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Response tracking (30-day SLA - EU-04)
    response_deadline = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending", index=True)  # "pending", "in_progress", "completed", "denied"
    
    # Reason (optional for delete requests)
    reason = Column(String, nullable=True)
    
    # Response details
    export_file_path = Column(String, nullable=True)  # File for access/export
    notes = Column(String, nullable=True)
    
    # Audit
    created_by = Column(String, default="user")  # "user" or "admin"


class RetentionPolicy(Base):
    """Configurable retention policies (EU-03)."""
    
    __tablename__ = "retention_policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    data_type = Column(String, nullable=False, unique=True)  # "posture_data", "logs", "biometric", etc.
    retention_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(String, nullable=True)


# ============================================================================
# PYDANTIC MODELS (API Request/Response)
# ============================================================================

class UserCreateRequest(BaseModel):
    """User creation request with mandatory consent."""
    
    email: Optional[str] = None
    region: str = Field(default="EU", description="EU, US, CA, or MX")
    date_of_birth: Optional[datetime] = None
    consent_given: bool = Field(default=False, description="Must be True to proceed")
    consent_version: str = Field(default="1.0")


class UserResponse(BaseModel):
    """User data response."""
    
    id: str
    email: Optional[str]
    created_at: datetime
    consent_given_at: Optional[datetime]
    region: str
    
    class Config:
        from_attributes = True


class PostureDataRequest(BaseModel):
    """Posture data submission."""
    
    spine_angle: Optional[float] = None
    shoulder_symmetry: Optional[float] = None
    neck_angle: Optional[float] = None
    alert_triggered: bool = False
    alert_level: Optional[str] = None
    session_id: Optional[str] = None


class PostureDataResponse(BaseModel):
    """Posture data response."""
    
    id: str
    timestamp: datetime
    spine_angle: Optional[float]
    shoulder_symmetry: Optional[float]
    neck_angle: Optional[float]
    alert_triggered: bool
    processing_model: str
    
    class Config:
        from_attributes = True


class ConsentUpdateRequest(BaseModel):
    """Update user consent."""
    
    consent_given: bool
    consent_version: str = "1.0"
    reason: Optional[str] = None


class DSARRequestCreate(BaseModel):
    """Create DSAR request."""
    
    request_type: str = Field(..., description="access, delete, export, or correct")
    reason: Optional[str] = None


class DSARRequestResponse(BaseModel):
    """DSAR request response."""
    
    id: str
    request_type: str
    requested_at: datetime
    response_deadline: datetime
    status: str
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Audit log response."""
    
    id: str
    timestamp: datetime
    event_type: str
    action: str
    status: str
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True
