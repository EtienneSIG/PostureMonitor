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

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, WebSocket, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import logging
from typing import List, Optional
import uuid
import cv2
import numpy as np
import asyncio
import json as json_lib
import math

# Import local modules
from backend.config import (
    ComplianceConfig, DatabaseConfig, APIConfig, CameraConfig,
    PRIVACY_NOTICE_EN, PRIVACY_NOTICE_FR, CONSENT_TEXT_EN, CONSENT_TEXT_FR
)
from backend.models import (
    Base, User, PostureData, ConsentLog, AuditLog, DSARRequest, RetentionPolicy,
    UserCreateRequest, UserResponse, PostureDataResponse,
    ConsentUpdateRequest, DSARRequestCreate, DSARRequestResponse, AuditLogResponse,
    LoginRequest, ResetPasswordRequest
)
from posture_analyzer import PostureAnalyzer

# Password hashing (local accounts) — bcrypt directly to avoid passlib/bcrypt
# version incompatibilities.
import bcrypt
import secrets


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def generate_recovery_code() -> str:
    """Generate a human-readable recovery code: 4 groups of 4 uppercase chars.

    Excludes ambiguous characters (0/O, 1/I) for easier manual entry.
    """
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    groups = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
    return "-".join(groups)


def normalize_recovery_code(code: str) -> str:
    """Normalize a recovery code for comparison (uppercase, no spaces)."""
    return (code or "").strip().upper().replace(" ", "")

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


def _ensure_schema():
    """Lightweight migration: add columns that may be missing on existing DBs."""
    from sqlalchemy import text
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)"))]
        if "password_hash" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
            conn.commit()
            logger.info("Migration: added users.password_hash column")
        if "recovery_code_hash" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN recovery_code_hash VARCHAR"))
            conn.commit()
            logger.info("Migration: added users.recovery_code_hash column")


_ensure_schema()

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
analyzer = None
analyzer_init_error = None
try:
    analyzer = PostureAnalyzer()
except Exception as exc:
    analyzer_init_error = str(exc)
    logger.warning("Posture analyzer unavailable at startup: %s", analyzer_init_error)


def serialize_model(schema, instance):
    """Compat helper for Pydantic v1/v2 style model serialization."""
    if hasattr(schema, "model_validate"):
        return schema.model_validate(instance)
    return schema.from_orm(instance)


def summarize_analysis(frame: np.ndarray) -> dict:
    """Normalize analyzer output into API-facing posture metrics."""
    if analyzer is None:
        raise RuntimeError(
            "Posture analyzer is unavailable. MediaPipe legacy pose support is missing in the current Python environment."
        )

    analysis = analyzer.analyze_posture(frame)
    angles = analysis.get("angles", {})
    key_points = analysis.get("key_points", {})
    issues = analysis.get("issues", [])
    confidence = analysis.get("confidence", 0.0)

    def _to_deg(horizontal: float, vertical: float) -> float:
        # Convert normalized landmark offsets into a geometric angle in degrees.
        if vertical <= 1e-6:
            return 90.0
        return math.degrees(math.atan2(abs(horizontal), vertical))

    def _clamp01(value: float) -> float:
        """Clamp value to [0, 1] range."""
        return max(0.0, min(1.0, value))

    # Estimate forehead from eyes + nose when available.
    forehead = None
    if all(k in key_points for k in ("left_eye", "right_eye", "nose")):
        left_eye = key_points["left_eye"]
        right_eye = key_points["right_eye"]
        nose = key_points["nose"]
        eye_mid_x = (left_eye[0] + right_eye[0]) / 2.0
        eye_mid_y = (left_eye[1] + right_eye[1]) / 2.0
        # Extend from nose toward eye center to approximate forehead center.
        forehead_x = eye_mid_x + (eye_mid_x - nose[0]) * 0.8
        forehead_y = eye_mid_y + (eye_mid_y - nose[1]) * 0.8
        forehead = (_clamp01(forehead_x), _clamp01(forehead_y))
        key_points["forehead"] = forehead

    spine_angle = None
    neck_angle = None
    shoulder_symmetry = None

    if all(k in key_points for k in ("left_shoulder", "right_shoulder")):
        left_shoulder = key_points["left_shoulder"]
        right_shoulder = key_points["right_shoulder"]
        shoulder_mid_x = (left_shoulder[0] + right_shoulder[0]) / 2.0
        shoulder_mid_y = (left_shoulder[1] + right_shoulder[1]) / 2.0

        shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
        shoulder_symmetry = max(0.0, 100.0 - min(shoulder_diff * 1000.0, 100.0))

        # Use forehead if available, otherwise use nose
        head_anchor = forehead or key_points.get("nose")
        if head_anchor:
            # Postural alignment angle, craniovertebral-angle (CVA) convention:
            # 90 deg = head perfectly stacked above the shoulders (ideal upright).
            # The angle decreases as the head deviates forward/sideways. In the
            # posture literature, forward head posture is defined by a *reduced*
            # angle, so higher is better here.
            deviation = _to_deg(head_anchor[0] - shoulder_mid_x, shoulder_mid_y - head_anchor[1])
            spine_angle = max(0.0, 90.0 - deviation)

        if "left_ear" in key_points and "right_ear" in key_points and "nose" in key_points:
            left_ear = key_points["left_ear"]
            right_ear = key_points["right_ear"]
            nose = key_points["nose"]
            ear_mid_x = (left_ear[0] + right_ear[0]) / 2.0
            ear_mid_y = (left_ear[1] + right_ear[1]) / 2.0
            
            # Neck angle: Measure the angle between shoulder and neck (ear level)
            # Also factor in the nose position for better forward/backward detection
            # Combine ear and nose reference point for robustness
            neck_ref_x = (ear_mid_x + nose[0]) / 2.0
            neck_ref_y = (ear_mid_y + nose[1]) / 2.0
            
            # Primary neck angle: ear-to-shoulder
            neck_angle = _to_deg(ear_mid_x - shoulder_mid_x, shoulder_mid_y - ear_mid_y)
            
            # Secondary neck forward/backward angle: if nose is far from shoulders, neck is bent
            # A value > 0 indicates forward bend, < 0 indicates backward (rare)
            nose_to_shoulder_dy = shoulder_mid_y - neck_ref_y
            # If nose is close to shoulder vertically, neck is very bent forward
            if nose_to_shoulder_dy < 0.05:  # Very close to shoulder = strong forward bend
                neck_angle = min(90.0, neck_angle + 20.0)  # Boost angle to reflect forward bend

    # Fallback to analyzer-provided values for compatibility.
    if spine_angle is None:
        if angles.get("head_shoulder_angle") is not None:
            spine_angle = float(angles["head_shoulder_angle"])
        elif angles.get("head_forward") is not None:
            spine_angle = abs(float(angles["head_forward"])) * 180.0

    if neck_angle is None:
        if angles.get("neck_angle") is not None:
            neck_angle = float(angles["neck_angle"])
        elif angles.get("head_tilt") is not None:
            neck_angle = abs(float(angles["head_tilt"])) * 180.0

    if shoulder_symmetry is None:
        if angles.get("shoulder_slope") is not None:
            shoulder_symmetry = max(0.0, 100.0 - min(abs(float(angles["shoulder_slope"])) * 100.0, 100.0))
        elif angles.get("shoulder_alignment") is not None:
            shoulder_symmetry = max(0.0, 100.0 - min(abs(float(angles["shoulder_alignment"])) * 1000.0, 100.0))

    # Calculate head tilt angles (left/right and forward/backward)
    head_tilt_lr = None  # Left/Right tilt in degrees
    head_forward_tilt = None  # Forward/Backward tilt in degrees

    # Head tilt left/right: Use eyes or ears to determine head rotation
    if all(k in key_points for k in ("left_eye", "right_eye")):
        left_eye = key_points["left_eye"]
        right_eye = key_points["right_eye"]
        # Calculate angle of the eye line relative to horizontal (0 degrees = level)
        eye_dy = right_eye[1] - left_eye[1]
        eye_dx = right_eye[0] - left_eye[0]
        if abs(eye_dx) > 1e-6:
            head_tilt_lr = math.degrees(math.atan(eye_dy / eye_dx))
            # Positive = right eye lower (tilt left), Negative = left eye lower (tilt right)
    elif all(k in key_points for k in ("left_ear", "right_ear")):
        left_ear = key_points["left_ear"]
        right_ear = key_points["right_ear"]
        ear_dy = right_ear[1] - left_ear[1]
        ear_dx = right_ear[0] - left_ear[0]
        if abs(ear_dx) > 1e-6:
            head_tilt_lr = math.degrees(math.atan(ear_dy / ear_dx))

    # Head tilt forward/backward: Compare head position to shoulder position
    if (forehead or key_points.get("nose")) and all(k in key_points for k in ("left_shoulder", "right_shoulder")):
        head_anchor = forehead or key_points.get("nose")
        left_shoulder = key_points["left_shoulder"]
        right_shoulder = key_points["right_shoulder"]
        shoulder_mid_y = (left_shoulder[1] + right_shoulder[1]) / 2.0
        
        # Forward tilt: If head is far forward, the horizontal distance from center is large
        # Backward tilt: If head is too far back (rare), head would be closer to shoulder vertically
        head_to_shoulder_dy = shoulder_mid_y - head_anchor[1]  # Positive = shoulder below head (normal)
        
        # If eyes and ears exist, use them to gauge head inclination
        if all(k in key_points for k in ("left_eye", "right_eye", "left_ear", "right_ear")):
            left_eye = key_points["left_eye"]
            right_eye = key_points["right_eye"]
            left_ear = key_points["left_ear"]
            right_ear = key_points["right_ear"]
            
            # Eye vertical center
            eye_y = (left_eye[1] + right_eye[1]) / 2.0
            ear_y = (left_ear[1] + right_ear[1]) / 2.0
            
            # Distance from eyes to shoulders (negative = forward)
            eye_to_shoulder = shoulder_mid_y - eye_y
            ear_to_shoulder = shoulder_mid_y - ear_y
            
            # A forward-tilted head means the ear is closer to shoulder (smaller distance)
            # Backward-tilted head means the ear is further from shoulder (larger distance)
            # Normalize to -90 to 90 degrees range
            if ear_to_shoulder >= 0:
                # Normal position: 0 degrees (ear above shoulder)
                # Maximum forward tilt: ~45 degrees (ear near shoulder level)
                head_forward_tilt = min(45.0, max(0.0, 45.0 * (1.0 - ear_to_shoulder / 0.15)))
            else:
                # Backward tilt (ear below shoulder) - this is abnormal
                head_forward_tilt = max(-45.0, min(0.0, -45.0 * abs(ear_to_shoulder) / 0.1))

    raw_key_points = analysis.get("key_points", {}) or {}
    tracked_keys = [
        "forehead",
        "nose",
        "left_eye",
        "right_eye",
        "left_ear",
        "right_ear",
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
    ]
    key_points_filtered = {
        key: raw_key_points[key]
        for key in tracked_keys
        if key in raw_key_points
    }

    return {
        "spine_angle": spine_angle,
        "shoulder_symmetry": shoulder_symmetry,
        "neck_angle": neck_angle,
        "head_tilt_lr": head_tilt_lr,
        "head_forward_tilt": head_forward_tilt,
        "alert": not analysis.get("good_posture", True),
        "issues": issues,
        "confidence": confidence,
        "key_points": key_points_filtered,
    }


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


async def get_current_user(
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> User:
    """Get current user with consent check."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")

    user = db.query(User).filter(User.id == x_user_id).first()
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
    Register new user with mandatory consent and optional password.
    
    Compliance notes:
    - Explicit consent required
    - Age check for COPPA
    - Password hashed with bcrypt if provided
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
    
    # Email uniqueness check (if email provided)
    if req.email:
        existing = db.query(User).filter(User.email == req.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    # Password validation (if password provided)
    if req.password:
        if len(req.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Generate a recovery code for offline password reset (only if password set)
    recovery_code = None
    recovery_code_hash = None
    if req.password:
        recovery_code = generate_recovery_code()
        recovery_code_hash = hash_password(recovery_code)
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        email=req.email,
        password_hash=hash_password(req.password) if req.password else None,
        recovery_code_hash=recovery_code_hash,
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
    
    # Return recovery code ONCE so the user can save it
    response = serialize_model(UserResponse, user)
    response.recovery_code = recovery_code
    return response


@app.post("/api/users/login", response_model=UserResponse)
async def login_user(
    req: LoginRequest,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Local login with email + password. Returns user profile if credentials match.
    """
    
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        log_audit(db, "LOGIN", "failed", status="failed", error_message="Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if user.deleted_at:
        raise HTTPException(status_code=410, detail="Account has been deleted")
    
    if not user.consent_given_at:
        raise HTTPException(status_code=403, detail="User must provide consent first")
    
    # Update last active
    user.last_active_at = datetime.utcnow()
    db.commit()
    
    log_audit(db, "LOGIN", "success", user.id)
    
    return serialize_model(UserResponse, user)


@app.post("/api/users/reset-password", response_model=UserResponse)
async def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Offline password reset using the recovery code issued at registration.

    Returns a NEW recovery code (single use) on success so the previous one
    cannot be reused.
    """

    # Validate new password
    if len(req.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = db.query(User).filter(User.email == req.email).first()
    if (
        not user
        or not user.recovery_code_hash
        or not verify_password(normalize_recovery_code(req.recovery_code), user.recovery_code_hash)
    ):
        log_audit(db, "PASSWORD_RESET", "failed", status="failed", error_message="Invalid recovery code")
        raise HTTPException(status_code=401, detail="Invalid email or recovery code")

    if user.deleted_at:
        raise HTTPException(status_code=410, detail="Account has been deleted")

    # Set new password and rotate the recovery code
    new_recovery_code = generate_recovery_code()
    user.password_hash = hash_password(req.new_password)
    user.recovery_code_hash = hash_password(new_recovery_code)
    user.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    log_audit(db, "PASSWORD_RESET", "success", user.id)

    response = serialize_model(UserResponse, user)
    response.recovery_code = new_recovery_code
    return response


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user: User = Depends(get_current_user),
) -> UserResponse:
    """Get user profile."""
    return serialize_model(UserResponse, user)


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

    if analyzer is None:
        await websocket.close(code=1011, reason="Posture analyzer unavailable in current environment")
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
            results = summarize_analysis(frame)
            posture_data = {
                "spine_angle": results.get("spine_angle"),
                "shoulder_symmetry": results.get("shoulder_symmetry"),
                "neck_angle": results.get("neck_angle"),
                "alert": results.get("alert", False),
                "issues": results.get("issues", []),
                "confidence": results.get("confidence", 0.0),
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
        try:
            await websocket.close()
        except RuntimeError:
            # Socket may already be closed when client disconnects quickly.
            pass


@app.post("/api/posture/analyze")
async def analyze_posture(
    file: UploadFile = File(...),
    user_id: str = None,
    session_id: str = None,
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

    try:
        results = summarize_analysis(frame)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    
    # Store aggregated metrics only
    posture = PostureData(
        user_id=user_id or user.id,
        session_id=session_id,
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
    
    return [serialize_model(PostureDataResponse, d) for d in data]


@app.get("/api/posture/stats")
async def get_posture_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Aggregated posture statistics for the dashboard."""

    week_ago = datetime.utcnow() - timedelta(days=7)

    # All records for this user in the last 7 days
    records = db.query(PostureData)\
        .filter(PostureData.user_id == user.id)\
        .filter(PostureData.timestamp >= week_ago)\
        .all()

    # Count distinct sessions (records without a session_id count as one legacy session)
    session_ids = {r.session_id for r in records if r.session_id}
    has_legacy = any(r.session_id is None for r in records)
    total_sessions = len(session_ids) + (1 if has_legacy else 0)

    alert_count = sum(1 for r in records if r.alert_triggered)

    spine_values = [r.spine_angle for r in records if r.spine_angle is not None]
    avg_spine_angle = sum(spine_values) / len(spine_values) if spine_values else 0.0

    symmetry_values = [r.shoulder_symmetry for r in records if r.shoulder_symmetry is not None]
    best_posture = max(symmetry_values) if symmetry_values else 0.0

    log_audit(db, "DATA_ACCESS", "stats_retrieved", user.id, resource="posture_stats")

    return {
        "total_sessions": total_sessions,
        "alert_count": alert_count,
        "avg_spine_angle": round(avg_spine_angle, 1),
        "best_posture": round(best_posture, 1),
        "total_records": len(records),
    }


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
    
    db.refresh(dsar)
    return serialize_model(DSARRequestResponse, dsar)


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
        ],
        "audit_log_count": db.query(AuditLog).filter(AuditLog.user_id == user.id).count()
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
    
    return [serialize_model(AuditLogResponse, l) for l in logs]


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
        "compliance": ["GDPR", "CCPA/CPRA", "BIPA", "PIPEDA", "COPPA"],
        "posture_analyzer_available": analyzer is not None,
        "posture_analyzer_error": analyzer_init_error,
    }


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy" if analyzer is not None else "degraded",
        "posture_analyzer_available": analyzer is not None,
        "posture_analyzer_error": analyzer_init_error,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=APIConfig.HOST, port=APIConfig.PORT, reload=APIConfig.RELOAD)
