# Posture Monitor Pro v2.0.0 - Architecture

## 🏗️ Modern Stack

```
┌─────────────────────────────────────────────┐
│     Frontend (Vue 3 + Vite)                │
│  http://localhost:5173                      │
├─────────────────────────────────────────────┤
│  Dashboard | Monitor | Privacy Center       │
│  - Consent Gate (Mandatory)                 │
│  - Age Verification (COPPA)                 │
│  - Real-time WebSocket posture stream       │
│  - DSAR interface (export/delete)           │
│  - Multi-language (EN/FR)                   │
└────────────────┬────────────────────────────┘
                 │ HTTP + WebSocket
                 ↓ (127.0.0.1:8000)
┌─────────────────────────────────────────────┐
│    Backend (FastAPI)                        │
│  http://127.0.0.1:8000                      │
├─────────────────────────────────────────────┤
│  - User management + consent                │
│  - Real-time posture analysis               │
│  - DSAR endpoints (access/delete)           │
│  - Audit logging                            │
│  - Data retention & cleanup                 │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│    Local Database (SQLite)                  │
│  posture_monitor.db                         │
├─────────────────────────────────────────────┤
│  - users (with consent tracking)            │
│  - posture_data (with TTL)                  │
│  - consent_logs (audit trail)               │
│  - audit_logs (1-year retention)            │
│  - dsar_requests (tracking)                 │
└─────────────────────────────────────────────┘
```

## 📁 Project Structure

```
PostureMonitor/
├── launch.py                    # 🚀 Unified launcher (both servers)
├── requirements.txt             # Python deps (FastAPI + analysis)
├── reglementation.md           # 🔒 Compliance tracking
│
├── backend/                    # FastAPI Backend
│   ├── app.py                  # Main application
│   ├── config.py               # Compliance settings (EU-01..NA-07)
│   ├── models.py               # DB models + Pydantic schemas
│   ├── __init__.py
│   ├── README.md
│   ├── .gitignore
│   └── posture_monitor.db      # SQLite (created on first run)
│
├── frontend/                   # Vue 3 + Vite
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.js
│   │   ├── style.css
│   │   ├── App.vue              # Main app + routing
│   │   ├── components/
│   │   │   ├── ConsentGate.vue  # Mandatory consent (EU-02, EU-05)
│   │   │   └── AgeGate.vue      # Age check (COPPA - NA-04)
│   │   ├── pages/
│   │   │   ├── Dashboard.vue     # Stats & history
│   │   │   ├── PostureMonitor.vue # Live monitoring
│   │   │   └── PrivacyCenter.vue  # DSAR + data mgmt (EU-04, NA-02)
│   │   └── stores/
│   │       └── userStore.js      # Pinia state
│   ├── README.md
│   ├── .gitignore
│   └── node_modules/            # npm packages
│
└── [existing Python files]
    ├── posture_analyzer.py
    ├── posture_alerts.py
    ├── posture_translator.py
    └── ...
```

## 🚀 Getting Started

### 1. Install Dependencies

```bash
# Python backend + analysis
pip install -r requirements.txt
```

### 2. Run Everything

```bash
# Launcher starts both backend and frontend
python launch.py
```

### 3. Open Browser

```
http://localhost:5173
```

### 4. Register

- Accept consent (mandatory)
- Verify age (13+)
- Start monitoring

## 🔐 Privacy & Compliance

**Built-in from day one:**

### Europe (GDPR)
- ✅ EU-01: Data inventory & minimization
- ✅ EU-02: Explicit consent with legal basis
- ✅ EU-03: Automatic data retention & cleanup
- ✅ EU-04: DSAR endpoints (access/export/delete)
- ✅ EU-05: No cookies/trackers
- ✅ EU-06: Comprehensive audit logging
- ✅ EU-07: Non-medical claims (verified)

### North America
- ✅ NA-02: CCPA/CPRA rights (export/delete)
- ✅ NA-03: BIPA biometric consent
- ✅ NA-04: COPPA age verification
- ✅ NA-05: PIPEDA (Canada)

**Key Features:**
- 🔒 All data processed locally
- 🔒 No video frames stored (in-memory only)
- 🔒 90-day data retention with auto-delete
- 🔒 1-year audit log retention
- 🔒 User can export/delete anytime
- 🔒 Transparent logging of all data access

## 🔌 API Endpoints

### User Management
```
POST   /api/users/register              # Create user (consent required)
GET    /api/users/{user_id}             # Get profile
PUT    /api/users/{user_id}/consent     # Update consent
```

### Posture Monitoring
```
WebSocket  /ws/posture/{user_id}        # Real-time stream
POST   /api/posture/analyze             # Analyze single image
GET    /api/posture/history             # Get history
```

### DSAR (Data Subject Access Requests)
```
POST   /api/dsar/request                # Create DSAR
GET    /api/dsar/export                 # Export all data
DELETE /api/users/{user_id}/data        # Delete all data
```

### Privacy
```
GET    /api/privacy/policy/{lang}       # Get privacy notice
GET    /api/privacy/consent-text/{lang} # Get consent text
```

### Audit
```
GET    /api/audit-logs                  # View audit trail
POST   /api/admin/cleanup               # Trigger cleanup job
```

## 🧪 Development Workflow

### Backend Development

```bash
# Terminal 1: Backend only
python launch.py --backend-only

# API docs: http://127.0.0.1:8000/docs
```

### Frontend Development

```bash
# Terminal 2: Frontend only
python launch.py --frontend-only

# App: http://localhost:5173
```

### Testing Flow

1. **Consent Check** → Open app, should see consent gate
2. **Age Check** → Submit DOB (13+)
3. **Dashboard** → Should show empty history
4. **Monitor** → Start WebSocket stream
5. **Privacy Center** → Export/delete should work
6. **Logout** → Should clear session

## 📊 Database Schema

### users
- `id` (UUID, PK)
- `email` (optional)
- `created_at`, `last_active_at`
- `consent_given_at`, `consent_withdrawn_at`
- `date_of_birth` (optional, for COPPA)
- `region` (EU, US, CA, MX)

### posture_data
- `id` (UUID, PK)
- `user_id` (FK to users)
- `timestamp` (indexed)
- `spine_angle`, `shoulder_symmetry`, `neck_angle`
- `alert_triggered`, `alert_level`
- `delete_at` (TTL - 90 days) - **AUTO-CLEANUP**

### consent_logs
- `id` (UUID, PK)
- `user_id` (indexed)
- `timestamp` (indexed)
- `action` (given/withdrawn/updated)
- `delete_at` (TTL - 1 year)

### audit_logs
- `id` (UUID, PK)
- `timestamp` (indexed)
- `event_type`, `action`
- `user_id`, `resource`, `status`
- `delete_at` (1 year - NEVER AUTO-DELETE)

### dsar_requests
- `id` (UUID, PK)
- `user_id` (indexed)
- `request_type` (access/delete/export)
- `requested_at`, `response_deadline` (30 days)
- `status` (pending/in_progress/completed)

## 🔧 Configuration

All compliance settings in `backend/config.py`:

```python
# Data retention (EU-03)
DATA_RETENTION_DAYS = 90
LOG_RETENTION_DAYS = 365
BIOMETRIC_DATA_RETENTION_DAYS = 7

# Consent & legal basis (EU-02, EU-05)
REQUIRE_EXPLICIT_CONSENT = True
CONSENT_VERSIONS = {...}

# Age gate (COPPA - NA-04)
REQUIRE_AGE_GATE = True
MINIMUM_AGE = 13

# User rights (EU-04, NA-02)
ENABLE_DATA_EXPORT = True
ENABLE_DATA_DELETION = True
DSAR_RESPONSE_DAYS = 30

# Logging & audit (EU-06, NA-06)
ENABLE_AUDIT_LOGGING = True
LOG_CONSENT_CHANGES = True
LOG_DSAR_REQUESTS = True
```

## 📈 Monitoring & Maintenance

### Daily Tasks
- Monitor error logs
- Check WebSocket stability

### Weekly Tasks
- Review audit logs
- Verify DSAR fulfillment

### Monthly Tasks
- Data retention cleanup
- Performance metrics
- Compliance audit

### Scheduled Jobs (implement with APScheduler)
```python
# Run daily at 2 AM
POST /api/admin/cleanup  # Deletes expired data
```

## 🚢 Production Deployment

### Prerequisites
1. Python 3.11+
2. Node.js 18+
3. PostgreSQL (optional, instead of SQLite)
4. SSL certificate

### Steps

```bash
# 1. Install dependencies
pip install -r requirements.txt
npm install --prefix frontend

# 2. Build frontend
npm run build --prefix frontend

# 3. Start backend (production)
python -m uvicorn backend.app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --ssl-keyfile=/path/to/key.pem \
  --ssl-certfile=/path/to/cert.pem

# 4. Serve frontend (via nginx/Apache)
# Point to frontend/dist/
```

### Security Checklist
- [ ] HTTPS enforced
- [ ] CORS restricted
- [ ] Rate limiting enabled
- [ ] API authentication added
- [ ] Database backups scheduled
- [ ] Audit logs archived
- [ ] Error monitoring setup (Sentry)

## 📚 Documentation

- `backend/README.md` - Backend API docs
- `frontend/README.md` - Frontend development
- `reglementation.md` - Compliance tracking
- `backend/config.py` - Compliance settings with comments

## 🤝 Contributing

1. Create feature branch
2. Update `reglementation.md` if adding new data processing
3. Test DSAR endpoints (export/delete)
4. Verify audit logging
5. Submit PR

## 📄 License

See LICENSE file
