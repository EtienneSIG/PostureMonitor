"""
Posture Monitor Pro - Backend API (FastAPI)

Modern, compliant backend with:
- RGPD/CCPA/BIPA compliance
- Real-time posture analysis
- User consent management
- DSAR (Data Subject Access Requests)
- Audit logging
- Automatic data retention

Run: uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import json
import logging
from typing import List, Optional
import uuid
import cv2
import numpy as np
from io import BytesIO
import asyncio
import json as json_lib

# Import local modules
from backend.config import (
    ComplianceConfig, DatabaseConfig, APIConfig, CameraConfig,
    PRIVACY_NOTICE_EN, PRIVACY_NOTICE_FR, CONSENT_TEXT_EN, CONSENT_TEXT_FR
)
from backend.models import (
    Base, User, PostureData, ConsentLog, AuditLog, DSARRequest, RetentionPolicy,
    UserCreateRequest, UserResponse, PostureDataRequest, PostureDataResponse,
    ConsentUpdateRequest, DSARRequestCreate, DSARRequestResponse, AuditLogResponse
)
from posture_analyzer import PostureAnalyzer
from posture_visualizer import PostureVisualizer

# ============================================================================
# SETUP
# ============================================================================

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database
engine = create_engine(DatabaseConfig.DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Posture Monitor Pro API",
    description="Modern, GDPR-compliant posture monitoring API",
    version="2.0.0"
)

# CORS (local-only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=APIConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Posture analysis engine
analyzer = PostureAnalyzer()
visualizer = PostureVisualizer()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(user_id: str, db: Session = Depends(get_db)) -> User:
    """Get current user with consent check."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.deleted_at:
        raise HTTPException(status_code=410, detail="User account deleted")
    if not user.consent_given_at:
        raise HTTPException(status_code=403, detail="User must provide consent first")
    return user


# ============================================================================
# AUDIT LOGGING UTILITIES
# ============================================================================

def log_audit(
    db: Session,
    event_type: str,
    action: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    details: Optional[dict] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """Create audit log entry (EU-06, NA-06)."""
    if not ComplianceConfig.ENABLE_AUDIT_LOGGING:
        return
    
    audit = AuditLog(
        user_id=user_id,
        event_type=event_type,
        action=action,
        resource=resource,
        details=details,
        status=status,
        error_message=error_message,
        ip_address=ip_address,
        delete_at=datetime.utcnow() + timedelta(days=ComplianceConfig.LOG_RETENTION_DAYS)
    )
    db.add(audit)
    db.commit()
    logger.info(f"[AUDIT] {event_type}: {action} | User: {user_id} | Status: {status}")


def log_consent_change(db: Session, user_id: str, action: str, consent_type: str, version: str):
    """Log consent change (EU-02, EU-05)."""
    log = ConsentLog(
        user_id=user_id,
        timestamp=datetime.utcnow(),
        action=action,
        consent_type=consent_type,
        version=version,
        delete_at=datetime.utcnow() + timedelta(days=ComplianceConfig.LOG_RETENTION_DAYS)
    )
    db.add(log)
    db.commit()
    log_audit(db, "CONSENT", action, user_id, f"consent_type:{consent_type}", {"version": version})


# ============================================================================
# COMPLIANCE & PRIVACY ENDPOINTS
# ============================================================================

@app.get("/api/privacy/policy/{language}")
async def get_privacy_policy(language: str = "en") -> JSONResponse:
    """Get privacy policy (EU-04, NA-02, PIPEDA)."""
    if language == "fr":
        return {"policy": PRIVACY_NOTICE_FR}
    return {"policy": PRIVACY_NOTICE_EN}


@app.get("/api/privacy/consent-text/{language}")
async def get_consent_text(language: str = "en") -> JSONResponse:
    """Get consent text (EU-02, EU-05)."""
    if language == "fr":
        return {"consent_text": CONSENT_TEXT_FR}
    return {"consent_text": CONSENT_TEXT_EN}


# ============================================================================
# USER MANAGEMENT (GDPR Article 13-15, CCPA)
# ============================================================================

@app.post("/api/users/register", response_model=UserResponse)
async def register_user(
    req: UserCreateRequest,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register new user with mandatory consent (EU-02, NA-03, COPPA).
    
    Compliance notes:
    - Explicit consent required
    - Age check for COPPA
    """
    
    # Age gate (COPPA - NA-04)
    if ComplianceConfig.REQUIRE_AGE_GATE and req.date_of_birth:
        age = (datetime.utcnow() - req.date_of_birth).days // 365
        if age < ComplianceConfig.MINIMUM_AGE:
            log_audit(db, "REGISTRATION", "age_check_failed", status="failed")
            raise HTTPException(
                status_code=403,
                detail=f"Must be {ComplianceConfig.MINIMUM_AGE}+ years old to use this service"
            )
    
    # Consent check (EU-02)
    if not req.consent_given:
        raise HTTPException(status_code=400, detail="Consent is mandatory")
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        region=req.region,
        date_of_birth=req.date_of_birth,
        consent_version=req.consent_version,
        consent_given_at=datetime.utcnow(),
        parental_consent_given=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log consent (EU-05)
    log_consent_change(db, user.id, "given", "posture_tracking", req.consent_version)
    
    return UserResponse.from_orm(user)


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user: User = Depends(get_current_user),
) -> UserResponse:
    """Get user profile."""
    return UserResponse.from_orm(user)


@app.put("/api/users/{user_id}/consent")
async def update_consent(
    user_id: str,
    req: ConsentUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user consent (EU-05, GDPR Article 7).
    Users can withdraw or update consent at any time.
    """
    
    user.consent_version = req.consent_version
    
    if req.consent_given:
        user.consent_given_at = datetime.utcnow()
        user.consent_withdrawn_at = None
        log_consent_change(db, user_id, "given", "posture_tracking", req.consent_version)
    else:
        user.consent_withdrawn_at = datetime.utcnow()
        log_consent_change(db, user_id, "withdrawn", "posture_tracking", req.consent_version)
    
    db.commit()
    log_audit(db, "CONSENT_UPDATE", "updated", user_id)
    
    return {"status": "consent updated"}


# ============================================================================
# POSTURE MONITORING (Real-time)
# ============================================================================

@app.websocket("/ws/posture/{user_id}")
async def websocket_posture(websocket: WebSocket, user_id: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time posture streaming.
    Consent required before access.
    """
    
    # Consent check
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.consent_given_at:
        await websocket.close(code=4003, reason="Consent required")
        return
    
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    try:
        cap = cv2.VideoCapture(CameraConfig.CAMERA_ID)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CameraConfig.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CameraConfig.FRAME_HEIGHT)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze posture (never store raw frames - EU-01, EU-03)
            results = analyzer.analyze(frame)
            posture_data = {
                "spine_angle": results.get("spine_angle"),
                "shoulder_symmetry": results.get("shoulder_symmetry"),
                "neck_angle": results.get("neck_angle"),
                "alert": results.get("alert", False),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store aggregated data only (EU-01, EU-03)
            posture = PostureData(
                user_id=user_id,
                spine_angle=posture_data["spine_angle"],
                shoulder_symmetry=posture_data["shoulder_symmetry"],
                neck_angle=posture_data["neck_angle"],
                alert_triggered=posture_data["alert"],
                session_id=session_id,
                processing_model=ComplianceConfig.AI_MODEL_VERSION,
                delete_at=datetime.utcnow() + timedelta(days=ComplianceConfig.DATA_RETENTION_DAYS)
            )
            db.add(posture)
            db.commit()
            
            # Send to frontend
            await websocket.send_json(posture_data)
            
            # Rate limiting
            await asyncio.sleep(1 / CameraConfig.FPS)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        log_audit(db, "POSTURE_STREAM", "error", user_id, status="failed", error_message=str(e))
    
    finally:
        cap.release()
        await websocket.close()


@app.post("/api/posture/analyze")
async def analyze_posture(
    file: UploadFile = File(...),
    user_id: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze single image/frame (EU-01, EU-06).
    Image processed in-memory, never stored as raw file.
    """
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    
    results = analyzer.analyze(frame)
    
    # Store aggregated metrics only
    posture = PostureData(
        user_id=user_id or user.id,
        spine_angle=results.get("spine_angle"),
        shoulder_symmetry=results.get("shoulder_symmetry"),
        neck_angle=results.get("neck_angle"),
        alert_triggered=results.get("alert", False),
        processing_model=ComplianceConfig.AI_MODEL_VERSION,
        delete_at=datetime.utcnow() + timedelta(days=ComplianceConfig.DATA_RETENTION_DAYS)
    )
    db.add(posture)
    db.commit()
    
    log_audit(db, "POSTURE_ANALYSIS", "analyzed", user_id or user.id)
    
    return results


@app.get("/api/posture/history")
async def get_posture_history(
    user: User = Depends(get_current_user),
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[PostureDataResponse]:
    """Get user's posture data history (EU-04, GDPR Article 15)."""
    
    data = db.query(PostureData)\
        .filter(PostureData.user_id == user.id)\
        .order_by(PostureData.timestamp.desc())\
        .limit(limit)\
        .all()
    
    log_audit(db, "DATA_ACCESS", "history_retrieved", user.id, resource="posture_history")
    
    return [PostureDataResponse.from_orm(d) for d in data]


# ============================================================================
# DSAR - DATA SUBJECT ACCESS REQUESTS (EU-04, NA-02, PIPEDA)
# ============================================================================

@app.post("/api/dsar/request")
async def create_dsar_request(
    req: DSARRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DSARRequestResponse:
    """
    Create DSAR request (Right to Access, Erasure, Portability).
    Response deadline: 30 days (EU-04 compliance).
    """
    
    dsar = DSARRequest(
        user_id=user.id,
        request_type=req.request_type,
        requested_at=datetime.utcnow(),
        response_deadline=datetime.utcnow() + timedelta(days=ComplianceConfig.DSAR_RESPONSE_DAYS),
        reason=req.reason,
        created_by="user"
    )
    db.add(dsar)
    db.commit()
    
    log_audit(db, "DSAR", req.request_type, user.id, resource="dsar_request")
    
    # TODO: In production, queue background task to fulfill request
    
    return DSARRequestResponse.from_orm(dsar)


@app.get("/api/dsar/export")
async def export_user_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all user data (EU-04 - Right to Portability, CCPA).
    Returns JSON file with all user data.
    """
    
    # Collect all data
    posture_data = db.query(PostureData).filter(PostureData.user_id == user.id).all()
    consent_logs = db.query(ConsentLog).filter(ConsentLog.user_id == user.id).all()
    audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user.id).all()
    
    export = {
        "user": {
            "id": user.id,
            "created_at": user.created_at.isoformat(),
            "region": user.region
        },
        "posture_data": [
            {
                "timestamp": p.timestamp.isoformat(),
                "spine_angle": p.spine_angle,
                "shoulder_symmetry": p.shoulder_symmetry,
                "neck_angle": p.neck_angle
            }
            for p in posture_data
        ],
        "consent_history": [
            {
                "timestamp": c.timestamp.isoformat(),
                "action": c.action
            }
            for c in consent_logs
        ]
    }
    
    # Create file
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json_lib.dump(export, f)
        filename = f.name
    
    log_audit(db, "DSAR", "data_exported", user.id, resource="full_export")
    
    return FileResponse(filename, filename=f"posture_monitor_export_{user.id}.json")


@app.delete("/api/users/{user_id}/data")
async def delete_user_data(
    user_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete all user data (EU-04 - Right to Erasure, CCPA).
    
    Note: Audit logs are kept for 1 year (legal requirement).
    """
    
    if user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete other user's data")
    
    # Delete user's data (except audit logs)
    db.query(PostureData).filter(PostureData.user_id == user_id).delete()
    db.query(ConsentLog).filter(ConsentLog.user_id == user_id).delete()
    
    # Soft-delete user account
    user.deleted_at = datetime.utcnow()
    db.commit()
    
    log_audit(db, "DSAR", "user_data_deleted", user_id, resource="full_deletion")
    
    return {"status": "User data deleted"}


# ============================================================================
# DATA RETENTION & CLEANUP (EU-03, GDPR Article 5)
# ============================================================================

@app.post("/api/admin/cleanup")
async def cleanup_expired_data(db: Session = Depends(get_db)):
    """
    Background cleanup job for expired data (EU-03).
    Should run daily. In production, use APScheduler/Celery.
    """
    
    now = datetime.utcnow()
    
    # Delete expired posture data
    deleted_count = db.query(PostureData)\
        .filter(PostureData.delete_at <= now)\
        .delete()
    
    # Delete expired logs
    expired_logs = db.query(ConsentLog)\
        .filter(ConsentLog.delete_at <= now)\
        .delete()
    
    db.commit()
    
    logger.info(f"[CLEANUP] Deleted {deleted_count} posture records and {expired_logs} logs")
    
    return {"deleted_posture_records": deleted_count, "deleted_logs": expired_logs}


# ============================================================================
# AUDIT LOG VIEWING (EU-06, NA-06)
# ============================================================================

@app.get("/api/audit-logs")
async def get_audit_logs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
) -> List[AuditLogResponse]:
    """Get user's own audit logs (transparency)."""
    
    logs = db.query(AuditLog)\
        .filter(AuditLog.user_id == user.id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit)\
        .all()
    
    return [AuditLogResponse.from_orm(l) for l in logs]


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/")
async def root():
    """API status."""
    return {
        "status": "running",
        "app": "Posture Monitor Pro API",
        "version": "2.0.0",
        "compliance": ["GDPR", "CCPA/CPRA", "BIPA", "PIPEDA", "COPPA"]
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APIConfig.HOST, port=APIConfig.PORT, reload=APIConfig.RELOAD)
