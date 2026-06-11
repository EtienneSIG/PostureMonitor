# Posture Monitor Pro - Backend

FastAPI-based backend for real-time posture monitoring with GDPR/CCPA/BIPA compliance.

Note environnement:
- Python 3.12 est supporte via un fallback MediaPipe Tasks (`PoseLandmarker`) avec telechargement automatique du modele `.task`.
- Python 3.11 reste recommande si vous voulez rester au plus proche du pipeline historique base sur `mediapipe.solutions`.

## Features

- ✅ Real-time posture analysis via WebSocket
- ✅ GDPR-compliant data handling (EU-01 to EU-07)
- ✅ CCPA/CPRA compliance (NA-02)
- ✅ BIPA biometric data handling (NA-03)
- ✅ COPPA age verification (NA-04)
- ✅ DSAR (Data Subject Access Requests) - EU-04
- ✅ Automatic data retention & cleanup - EU-03
- ✅ Comprehensive audit logging - EU-06
- ✅ Privacy by design - local-first, no cloud

## Architecture

```
backend/
├── app.py              # Main FastAPI application
├── config.py           # Compliance configuration
├── models.py           # Database models & Pydantic schemas
└── requirements.txt    # Python dependencies
```

## Key Endpoints

### User Management
- `POST /api/users/register` - Create user with mandatory consent
- `GET /api/users/{user_id}` - Get user profile
- `PUT /api/users/{user_id}/consent` - Update consent

Authenticated API calls use the `X-User-Id` header after registration.

### Privacy & Compliance
- `GET /api/privacy/policy/{language}` - Get privacy notice
- `GET /api/privacy/consent-text/{language}` - Get consent text

### Posture Monitoring
- `WebSocket /ws/posture/{user_id}` - Real-time WebSocket stream
- `POST /api/posture/analyze` - Analyze single image
- `GET /api/posture/history` - Get user's posture history

On Python 3.12, posture analysis runs through MediaPipe Tasks using a local `pose_landmarker_full.task` model cached under `.cache/`.

### DSAR (Data Subject Access Requests)
- `POST /api/dsar/request` - Create DSAR request
- `GET /api/dsar/export` - Export all user data (Right to Portability)
- `DELETE /api/users/{user_id}/data` - Delete all user data (Right to Erasure)

### Audit & Maintenance
- `GET /api/audit-logs` - View audit logs
- `POST /api/admin/cleanup` - Trigger data retention cleanup

## Database

SQLite (default) - can be switched to PostgreSQL for production.

**Tables:**
- `users` - User accounts with consent tracking
- `posture_data` - Aggregated posture metrics (TTL-based cleanup)
- `consent_logs` - Audit trail for consent changes
- `audit_logs` - Comprehensive event logging
- `dsar_requests` - Data Subject Access Request tracking
- `retention_policies` - Configurable data retention rules

## Configuration

See `backend/config.py` for all compliance settings:
- Data retention periods (EU-03)
- Consent management (EU-02, EU-05)
- AI/biometric transparency (EU-06)
- Regional compliance (GDPR, CCPA/CPRA, BIPA, PIPEDA, COPPA)

## Compliance Mapping

| Regulation | Implemented In | Key Features |
|---|---|---|
| GDPR (EU-01-07) | models.py, app.py | Consent, DSAR, retention, audit logging |
| CCPA/CPRA (NA-02) | app.py endpoints | Data export, deletion, access requests |
| BIPA (NA-03) | config.py, models.py | Biometric data handling, explicit consent |
| COPPA (NA-04) | models.py, app.py | Age verification (13+) |
| PIPEDA (NA-05) | config.py | Canadian privacy compliance |

## Running

From project root:

```bash
# Both backend and frontend
python launch.py

# Backend only (for testing)
python launch.py --backend-only

# Then visit: http://localhost:5173
# API docs: http://127.0.0.1:8000/docs
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run backend with auto-reload
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload

# View API docs
# http://127.0.0.1:8000/docs
```

## Security Notes

- All data stored locally by default
- No cloud integration
- Video frames processed in-memory, never stored
- SQLite suitable for single-user local deployment
- Use PostgreSQL + HTTPS for multi-user production
- Implement rate limiting before production
- Add API key authentication if needed

## Compliance Checklist

See `reglementation.md` in project root for full compliance tracking.

Key items for backend:
- [ ] EU-01: Data inventory
- [ ] EU-03: TTL implementation for all data types
- [ ] EU-04: DSAR endpoints (export/delete)
- [ ] EU-06: Audit logging in place
- [ ] NA-03: Biometric consent required
- [ ] Cleanup job scheduled
