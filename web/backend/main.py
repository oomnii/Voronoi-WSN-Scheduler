from __future__ import annotations
from pathlib import Path
import sys, io, csv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.config import SimConfig
from src.simulator import run_voronoi, run_compare, experiment_density

FRONTEND_DIR = ROOT / "web" / "frontend"

app = FastAPI(title="Voronoi WSN Premium Dashboard", version="2.0")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

class SimRequest(BaseModel):
    n_nodes: int = 120
    width: float = 100.0
    height: float = 100.0
    sensing_radius: float = 15.0
    threshold_coeff: float = 0.02
    seed: int = 7
    enable_fault_tolerance: bool = True
    failure_prob_per_round: float = 0.02
    n_rounds: int = 50

def _cfg(req: SimRequest) -> SimConfig:
    return SimConfig(
        n_nodes=req.n_nodes,
        width=req.width,
        height=req.height,
        sensing_radius=req.sensing_radius,
        threshold_coeff=req.threshold_coeff,
        seed=req.seed,
        enable_fault_tolerance=req.enable_fault_tolerance,
        failure_prob_per_round=req.failure_prob_per_round,
        n_rounds=req.n_rounds,
    )

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/run")
def api_run(req: SimRequest):
    cfg = _cfg(req)
    points, boundary, active_mask, backups, metrics, fault_logs = run_voronoi(cfg)
    return {
        "points": points.tolist(),
        "active_mask": active_mask.tolist(),
        "backups": [int(x) for x in backups],
        "metrics": metrics,
        "fault_logs": fault_logs,
    }

@app.post("/api/compare")
def api_compare(req: SimRequest):
    cfg = _cfg(req)
    out = run_compare(cfg)
    return {
        "points": out["points"].tolist(),
        "voronoi": {
            "active_mask": out["voronoi"]["active_mask"].tolist(),
            "metrics": out["voronoi"]["metrics"],
            "fault_logs": out["voronoi"]["fault_logs"],
        },
        "random_same_off": {
            "active_mask": out["random_same_off"]["active_mask"].tolist(),
            "metrics": out["random_same_off"]["metrics"],
        },
        "random_greedy_cov": {
            "active_mask": out["random_greedy_cov"]["active_mask"].tolist(),
            "metrics": out["random_greedy_cov"]["metrics"],
        },
    }

@app.post("/api/experiment/density")
def api_density(req: SimRequest):
    cfg = _cfg(req)
    df = experiment_density(cfg)
    return {"rows": df.to_dict(orient="records")}

@app.post("/api/export/run.csv")
def export_run_csv(req: SimRequest):
    cfg = _cfg(req)
    points, boundary, active_mask, backups, metrics, fault_logs = run_voronoi(cfg)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["key", "value"])
    for k, v in metrics.items():
        writer.writerow([k, v])
    writer.writerow([])
    writer.writerow(["node_index", "x", "y", "state"])
    for i, (x, y) in enumerate(points.tolist()):
        writer.writerow([i, x, y, "ACTIVE" if bool(active_mask[i]) else "BACKUP_OFF"])

    csv_bytes = buf.getvalue().encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=wsn_run_export.csv"},
    )
