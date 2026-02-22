import numpy as np
from shapely.geometry import Polygon
from .metrics import compute_coverage_ratio
from .geometry import sensing_coverage_union

def simulate_failures_and_recovery(points: np.ndarray,
                                   boundary: Polygon,
                                   sensing_radius: float,
                                   active_mask_init: np.ndarray,
                                   backups: list[int],
                                   n_rounds: int,
                                   failure_prob: float,
                                   rng: np.random.Generator,
                                   target_coverage: float = 0.99):
    active = active_mask_init.copy()
    backup_set = set(int(x) for x in backups)
    logs = []

    for r in range(1, n_rounds + 1):
        active_idx = np.where(active)[0]
        failed = []
        if len(active_idx) and failure_prob > 0:
            mask = rng.random(len(active_idx)) < failure_prob
            failed = active_idx[mask].tolist()
            for fn in failed:
                active[int(fn)] = False
                backup_set.add(int(fn))

        cov = compute_coverage_ratio(points[active], sensing_radius, boundary)
        activated = []

        if cov < target_coverage and backup_set:
            while cov < target_coverage and backup_set:
                current_union = sensing_coverage_union(points[active], sensing_radius, boundary)
                best, best_gain = None, 0.0
                for b in list(backup_set):
                    candidate = current_union.union(
                        sensing_coverage_union(points[[b]], sensing_radius, boundary)
                    )
                    gain = candidate.area - current_union.area
                    if gain > best_gain + 1e-9:
                        best_gain, best = gain, b
                if best is None or best_gain <= 1e-9:
                    break
                active[best] = True
                backup_set.remove(best)
                activated.append(int(best))
                cov = compute_coverage_ratio(points[active], sensing_radius, boundary)

        logs.append({
            "round": r,
            "coverage": float(cov),
            "n_active": int(active.sum()),
            "n_backup_available": int(len(backup_set)),
            "failed": [int(x) for x in failed],
            "activated": activated
        })

    return active, list(backup_set), logs
