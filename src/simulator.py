import numpy as np
import pandas as pd

from .config import SimConfig
from .geometry import field_polygon, random_points
from .scheduling import (
    schedule_by_voronoi_threshold,
    schedule_random_same_off,
    schedule_random_greedy_coverage,
)
from .metrics import compute_coverage_ratio, energy_savings
from .fault_tolerance import simulate_failures_and_recovery

def run_voronoi(cfg: SimConfig):
    rng = np.random.default_rng(cfg.seed)
    boundary = field_polygon(cfg.width, cfg.height)
    points = random_points(cfg.n_nodes, cfg.width, cfg.height, rng)

    threshold_area = cfg.threshold_coeff * (np.pi * (cfg.sensing_radius ** 2))
    active_mask, backups = schedule_by_voronoi_threshold(points, boundary, threshold_area)

    cov_all = compute_coverage_ratio(points, cfg.sensing_radius, boundary)
    cov_sched = compute_coverage_ratio(points[active_mask], cfg.sensing_radius, boundary)

    energy = energy_savings(active_mask, cfg.energy_active_cost, cfg.energy_sleep_cost, rounds=1)

    result = {
        "algo": "Voronoi-Threshold",
        "n_nodes": cfg.n_nodes,
        "width": float(cfg.width),
        "height": float(cfg.height),
        "field_area": float(cfg.width * cfg.height),
        "density": float(cfg.n_nodes / (cfg.width * cfg.height)),
        "sensing_radius": float(cfg.sensing_radius),
        "threshold_coeff": float(cfg.threshold_coeff),
        "threshold_area": float(threshold_area),
        "coverage_all": float(cov_all),
        "coverage_scheduled": float(cov_sched),
        "n_backups": int(len(backups)),
        **energy
    }

    ft_logs = None
    if cfg.enable_fault_tolerance:
        target = min(0.99, cov_sched if cov_sched > 0 else 0.99)
        _, _, ft_logs = simulate_failures_and_recovery(
            points, boundary, cfg.sensing_radius, active_mask, backups,
            cfg.n_rounds, cfg.failure_prob_per_round, rng, target
        )

    return points, boundary, active_mask, backups, result, ft_logs

def run_compare(cfg: SimConfig):
    points, boundary, active_v, backups_v, res_v, ft_v = run_voronoi(cfg)
    rng = np.random.default_rng(cfg.seed + 999)

    active_r1, backups_r1 = schedule_random_same_off(points, boundary, cfg.sensing_radius, len(backups_v), rng)
    cov_r1 = compute_coverage_ratio(points[active_r1], cfg.sensing_radius, boundary)
    energy_r1 = energy_savings(active_r1, cfg.energy_active_cost, cfg.energy_sleep_cost, rounds=1)
    res_r1 = {"algo": "Random-Same-OFF", "coverage_scheduled": float(cov_r1), "n_backups": int(len(backups_r1)), **energy_r1}

    target = float(res_v["coverage_scheduled"])
    active_r2, backups_r2 = schedule_random_greedy_coverage(points, boundary, cfg.sensing_radius, target, rng)
    cov_r2 = compute_coverage_ratio(points[active_r2], cfg.sensing_radius, boundary)
    energy_r2 = energy_savings(active_r2, cfg.energy_active_cost, cfg.energy_sleep_cost, rounds=1)
    res_r2 = {"algo": "Random-Greedy-Coverage", "coverage_scheduled": float(cov_r2), "n_backups": int(len(backups_r2)), **energy_r2}

    return {
        "points": points, "boundary": boundary,
        "voronoi": {"active_mask": active_v, "backups": backups_v, "metrics": res_v, "fault_logs": ft_v},
        "random_same_off": {"active_mask": active_r1, "backups": backups_r1, "metrics": res_r1},
        "random_greedy_cov": {"active_mask": active_r2, "backups": backups_r2, "metrics": res_r2},
    }

def experiment_density(cfg: SimConfig, area_multipliers=(0.25, 0.5, 1.0, 2.0, 4.0)):
    rows = []
    for i, k in enumerate(area_multipliers):
        A = float(cfg.width * cfg.height) * float(k)
        side = float(A) ** 0.5
        local = SimConfig(**{**cfg.__dict__})
        local.width = side
        local.height = side
        local.seed = cfg.seed + i * 13
        _, _, _, backups, result, _ = run_voronoi(local)
        rows.append({
            "field_area": float(A),
            "density": float(result["density"]),
            "backup_nodes": int(len(backups)),
            "coverage": float(result["coverage_scheduled"]),
            "energy_saved_pct": float(result["energy_saved_pct"]),
        })
    return pd.DataFrame(rows)
