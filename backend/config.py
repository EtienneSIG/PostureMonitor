"""
Backend configuration for Posture Monitor Pro.

Compliance settings aligned with reglementation.md:
- EU: RGPD, ePrivacy, AI Act, MDR
- NA: CCPA/CPRA, BIPA, PIPEDA, COPPA
"""

import os
from datetime import timedelta
from typing import Dict

# ============================================================================
# COMPLIANCE & PRIVACY SETTINGS (EU-01 to NA-07)
# ============================================================================

class ComplianceConfig:
    """Compliance settings per jurisdiction."""
    
    # Data retention (EU-03, NA-02, NA-05)
    # Minimal retention for analytics and support; auto-deletion after
    DATA_RETENTION_DAYS: int = 90  # Keep raw posture data for 90 days
    LOG_RETENTION_DAYS: int = 365  # Keep audit logs for 1 year (legal requirement)
    
    # Biometric data (NA-03, BIPA, EU-01)
    # Frame images/video must be handled carefully
    BIOMETRIC_DATA_RETENTION_DAYS: int = 7  # Very short retention for video/images
    DELETE_VIDEO_FRAMES_AFTER_SECONDS: int = 10  # Delete raw frames immediately after processing
    STORE_VIDEO_LOCALLY: bool = False  # Never store raw video to disk (process in-memory)
    
    # Consent & Legal Basis (EU-02, EU-05, NA-02, NA-03)
    REQUIRE_EXPLICIT_CONSENT: bool = True  # Must explicitly accept before using
    CONSENT_VERSIONS: Dict[str, str] = {
        "1.0": "Initial consent (posture tracking only)",
        "1.1": "Updated consent (analytics for improvement)"
    }
    
    # Age gate (COPPA - NA-04)
    REQUIRE_AGE_GATE: bool = True
    MINIMUM_AGE: int = 13  # COPPA requirement
    REQUIRE_PARENTAL_CONSENT_UNDER_AGE: int = 13
    
    # User Rights (DSAR - EU-04, NA-02, NA-05)
    ENABLE_DATA_EXPORT: bool = True  # Right to portability
    ENABLE_DATA_DELETION: bool = True  # Right to erasure
    DSAR_RESPONSE_DAYS: int = 30  # 30 days to respond to DSAR (EU standard)
    
    # Logging & Audit (EU-06, EU-02, NA-06)
    ENABLE_AUDIT_LOGGING: bool = True  # Log all sensitive operations
    LOG_CONSENT_CHANGES: bool = True  # Track when user changes consent
    LOG_DSAR_REQUESTS: bool = True  # Track data subject access requests
    LOG_DATA_ACCESS: bool = True  # Log who accesses what data
    
    # AI & Biometric Transparency (EU-06, AI Act)
    ENABLE_AI_LOGGING: bool = True  # Log all ML/AI decisions
    AI_MODEL_VERSION: str = "mediapipe-pose-v1"
    DISCLOSE_AI_USAGE: bool = True  # Clearly disclose AI use in UI
    
    # Regional settings
    REGIONS_ENABLED: list = ["EU", "US", "CA"]  # Enabled jurisdictions


class DatabaseConfig:
    """Database configuration."""
    
    DB_URL: str = os.getenv("DATABASE_URL", "sqlite:///./posture_monitor.db")
    # Use SQLite locally, migrate to PostgreSQL in production if needed
    

class APIConfig:
    """API and server configuration."""
    
    HOST: str = "127.0.0.1"  # Local-only (privacy first)
    PORT: int = 8000
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    RELOAD: bool = os.getenv("RELOAD", "True").lower() == "true"
    
    # CORS settings (no remote access by default)
    CORS_ORIGINS: list = ["http://localhost:5173", "http://127.0.0.1:5173"]
    

class CameraConfig:
    """Camera/video processing configuration."""
    
    CAMERA_ID: int = 0  # Default camera
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    FPS: int = 30
    
    # Biometric data handling
    PROCESS_IN_MEMORY: bool = True  # Never store raw frames
    COMPRESS_BEFORE_TRANSMISSION: bool = True
    

class NotificationConfig:
    """Notification and alert settings."""
    
    ENABLE_POSTURE_ALERTS: bool = True
    ALERT_SOUND: bool = True
    ALERT_VISUAL: bool = True
    

# ============================================================================
# PRIVACY POLICY & LEGAL TEXT (EU-02, EU-04, NA-02, NA-05)
# ============================================================================

PRIVACY_NOTICE_EN = """
PRIVACY NOTICE - Posture Monitor Pro

DATA COLLECTED:
- Real-time posture metrics (spine angle, shoulder position, etc.)
- Session timestamps and duration
- Language and sensitivity preferences
- Consent and preferences data

LEGAL BASIS:
- Your explicit consent (Posture tracking)
- Legitimate interest (improving app stability)

YOUR RIGHTS:
- Access your data (export)
- Delete your data (erasure)
- Correct inaccurate data
- Withdraw consent at any time

DATA RETENTION:
- Posture data: 90 days
- Video frames: Deleted immediately after analysis
- Audit logs: 1 year
- Your data deleted upon request

LEGAL COMPLIANCE:
- GDPR (EU), CCPA/CPRA (US), PIPEDA (Canada)
- BIPA (Illinois) - Biometric data
- COPPA (Children <13)

CONTACT: [your-email@example.com]
"""

PRIVACY_NOTICE_FR = """
AVIS DE CONFIDENTIALITE - Posture Monitor Pro

DONNEES COLLECTEES:
- Metriques de posture en temps reel (angle de la colonne vertebrale, position des epaules, etc.)
- Horodatages et duree des sessions
- Preferences de langue et sensibilite
- Donnees de consentement

BASE JURIDIQUE:
- Votre consentement explicite (Suivi de la posture)
- Interet legitime (amelioration de la stabilite de l'application)

VOS DROITS:
- Acceder a vos donnees (export)
- Supprimer vos donnees (oubli)
- Corriger les donnees inexactes
- Retirer votre consentement a tout moment

RETENTION DES DONNEES:
- Donnees de posture: 90 jours
- Images video: Supprimees immediatement apres analyse
- Journaux d'audit: 1 an
- Vos donnees supprimees sur demande

CONFORMITE LEGALE:
- RGPD (UE), CCPA/CPRA (USA), PIPEDA (Canada)
- BIPA (Illinois) - Donnees biometriques
- COPPA (Enfants < 13)

CONTACT: [your-email@example.com]
"""

CONSENT_TEXT_EN = """
I understand and agree to:
1. Collection of my posture data for real-time monitoring
2. Processing of video frames (deleted immediately after analysis)
3. Storage of aggregated analytics data
4. Use of my data to improve the application
5. Compliance with GDPR, CCPA/CPRA, and BIPA regulations
"""

CONSENT_TEXT_FR = """
Je comprends et j'accepte:
1. La collecte de mes donnees de posture pour la surveillance en temps reel
2. Le traitement des images video (supprimees immediatement apres analyse)
3. Le stockage des donnees d'analytique aggregees
4. L'utilisation de mes donnees pour ameliorer l'application
5. La conformite avec les reglementations RGPD, CCPA/CPRA et BIPA
"""
