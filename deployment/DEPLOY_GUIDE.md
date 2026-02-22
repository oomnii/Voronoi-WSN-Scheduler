# Deploy Guide (Render / Railway)

Deploy as a single FastAPI service that serves the frontend.

## Docker (recommended)
Use `deployment/Dockerfile`.

### Render
- New Web Service → connect GitHub repo
- Environment: Docker
- Exposed port: 8000
- Open service URL → dashboard loads.

### Railway
- Deploy from GitHub
- Set start command (if needed):
  `uvicorn web.backend.main:app --host 0.0.0.0 --port $PORT`

## Non-Docker
Build: `pip install -r web/backend/requirements_web.txt`
Start: `uvicorn web.backend.main:app --host 0.0.0.0 --port 8000`
