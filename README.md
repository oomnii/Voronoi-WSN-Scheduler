# Voronoi WSN Scheduler — Premium Full-Stack Project

## Run locally
```bash
pip install -r web/backend/requirements_web.txt
python -m uvicorn web.backend.main:app --reload --port 8000
```
Open: http://localhost:8000

## Features
- Voronoi scheduling + backups
- Fault tolerance simulation
- Compare vs random baselines
- Density experiments (energy vs density)
- CSV exports
- Deploy guide + Dockerfile
