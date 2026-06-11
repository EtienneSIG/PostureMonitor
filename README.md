# Posture Monitor Pro

Application locale de suivi de posture avec interface moderne et exigences de conformite integrees.

## Demarrage rapide

### Application moderne recommandee
```bash
python launch.py
```

Puis ouvrir `http://localhost:5173`.

### Modes alternatifs
```bash
python launch.py --backend-only
python launch.py --frontend-only
python posture_monitor_gui.py
```

## Architecture

- `frontend/`: interface moderne Vue 3 + Vite
- `backend/`: API locale FastAPI + WebSocket
- `launch.py`: lanceur unique backend + frontend
- `reglementation.md`: suivi conformite Europe / North America
- `posture_monitor_gui.py`: ancienne interface desktop conservee en secours

## Fonctionnalites principales

- monitoring de posture en temps reel
- interface web locale plus simple d utilisation
- consentement explicite avant usage
- verification d age minimale
- export et suppression des donnees utilisateur
- logs d audit et retention des donnees
- support anglais / francais

## Conformite integree

- RGPD: consentement, droit d acces, suppression, retention
- ePrivacy: pas de traceurs tiers ajoutes
- BIPA / biometrie: consentement explicite avant traitement
- CCPA/CPRA: export et suppression des donnees
- COPPA: controle d age
- PIPEDA: approche privacy-first locale

## Fichiers importants

- `backend/app.py`: endpoints API et WebSocket
- `backend/config.py`: regles de retention et conformite
- `backend/models.py`: modeles de donnees et audit
- `frontend/src/pages/PostureMonitor.vue`: ecran principal de monitoring
- `frontend/src/pages/PrivacyCenter.vue`: gestion des droits utilisateur

## Installation

### Python
```bash
pip install -r requirements.txt
```

Python 3.12 est maintenant supporte via le backend MediaPipe Tasks moderne.
Python 3.11 reste le chemin le plus stable pour rester proche du backend historique et des anciennes integrations.

### Setup stable Python 3.11
```powershell
./setup_py311.ps1
```

Ce script prepare un environnement `.venv311` si Python 3.11 est installe localement.

### Node.js
Node.js 18+ est requis pour le frontend.

Au premier lancement, `launch.py` installe automatiquement les dependances frontend si necessaire.

## Notes

- le traitement reste local par defaut
- les frames video brutes ne doivent pas etre stockees durablement
- le README historique de la GUI desktop a ete remplace par cette vue d ensemble du repo
- sous Python 3.12, le modele `pose_landmarker_full.task` est telecharge automatiquement dans `.cache/` au premier demarrage
- l endpoint `/health` indique si l analyseur de posture est disponible

Voir aussi `backend/README.md`, `frontend/README.md` et `reglementation.md`.

