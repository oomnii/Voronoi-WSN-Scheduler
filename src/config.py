from dataclasses import dataclass

@dataclass
class SimConfig:
    width: float = 100.0
    height: float = 100.0

    n_nodes: int = 120
    sensing_radius: float = 15.0

    threshold_coeff: float = 0.02  # threshold_area = coeff * (pi * Rs^2)

    energy_active_cost: float = 1.0
    energy_sleep_cost: float = 0.05

    enable_fault_tolerance: bool = True
    failure_prob_per_round: float = 0.02
    n_rounds: int = 50

    seed: int = 7
