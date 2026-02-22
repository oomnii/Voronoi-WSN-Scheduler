import numpy as np
from shapely.geometry import Polygon
from .geometry import voronoi_areas
from .metrics import compute_coverage_ratio

def schedule_by_voronoi_threshold(points: np.ndarray, boundary: Polygon, threshold_area: float):
    n = len(points)
    active = np.ones(n, dtype=bool)
    backups: list[int] = []
    if threshold_area <= 0:
        return active, backups

    while True:
        active_idx = np.where(active)[0]
        if len(active_idx) <= 1:
            break
        areas = voronoi_areas(points[active_idx], boundary)
        m = int(np.argmin(areas))
        if float(areas[m]) < threshold_area:
            off = int(active_idx[m])
            active[off] = False
            backups.append(off)
        else:
            break
    return active, backups

def schedule_random_same_off(points: np.ndarray, boundary: Polygon, sensing_radius: float, n_off: int, rng: np.random.Generator):
    n = len(points)
    n_off = max(0, min(int(n_off), n-1))
    idx = np.arange(n)
    rng.shuffle(idx)
    off = set(idx[:n_off].tolist())
    active = np.array([i not in off for i in range(n)], dtype=bool)
    backups = list(off)
    return active, backups

def schedule_random_greedy_coverage(points: np.ndarray, boundary: Polygon, sensing_radius: float, target_coverage: float, rng: np.random.Generator):
    n = len(points)
    active = np.ones(n, dtype=bool)
    order = np.arange(n)
    rng.shuffle(order)
    for i in order:
        active[i] = False
        cov = compute_coverage_ratio(points[active], sensing_radius, boundary)
        if cov + 1e-9 < target_coverage:
            active[i] = True
    backups = np.where(~active)[0].tolist()
    return active, backups
