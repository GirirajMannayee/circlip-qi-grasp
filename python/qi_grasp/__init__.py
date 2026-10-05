"""Reference implementation for the circlip-to-sleeve QI grasp-selection manuscript."""
from .core import (N, WEIGHTS, cost, utility, soft_phases, hard_phases,
                   amplitude_search, grover_p, candidate_set_seed42, select)

__all__ = ["N", "WEIGHTS", "cost", "utility", "soft_phases", "hard_phases",
           "amplitude_search", "grover_p", "candidate_set_seed42", "select"]
__version__ = "1.0.0"
