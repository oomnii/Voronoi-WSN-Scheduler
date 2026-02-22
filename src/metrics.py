import numpy as np
from shapely.geometry import Polygon
from .geometry import sensing_coverage_union

def compute_coverage_ratio(points_active: np.ndarray, sensing_radius: float, boundary: Polygon) -> float:
    if len(points_active) == 0:
        return 0.0
    covered = sensing_coverage_union(points_active, sensing_radius, boundary)
    return float(covered.area / boundary.area)

def energy_savings(active_mask: np.ndarray, e_active: float, e_sleep: float, rounds: int = 1) -> dict:
    n = len(active_mask)
    n_on = int(active_mask.sum())
    n_off = n - n_on
    baseline = n * e_active * rounds
    scheduled = n_on * e_active * rounds + n_off * e_sleep * rounds
    saved = baseline - scheduled
    pct = 0.0 if baseline == 0 else 100.0 * saved / baseline
    return {
        "n_on": n_on,
        "n_off": n_off,
        "baseline_energy": float(baseline),
        "scheduled_energy": float(scheduled),
        "energy_saved": float(saved),
        "energy_saved_pct": float(pct),
    }
