"""Core numerics: Eq. (1)-(2) cost/utility, Eq. (10)-(12) amplitude search, Eq. (11) Grover law.

Mirrors Appendix B.1 of the manuscript. Feature order is
(E_p, E_theta, D_e, F_n, S_d), each in [0, 1].
"""
from __future__ import annotations
import numpy as np

N = 16
WEIGHTS = np.array([0.30, 0.25, 0.20, 0.15, 0.10])  # Eq. (1)


def cost(features: np.ndarray, weights: np.ndarray = WEIGHTS) -> np.ndarray:
    """Eq. (1): J(p) = 0.30 E'p + 0.25 E'theta + 0.20 D'e + 0.15 F'n + 0.10 S'd."""
    return np.asarray(features, float) @ weights


def utility(features: np.ndarray, weights: np.ndarray = WEIGHTS) -> np.ndarray:
    """Eq. (2): U = 1 - J."""
    return 1.0 - cost(features, weights)


def soft_phases(U: np.ndarray, gamma: float = 6.0) -> np.ndarray:
    """Eq. (12): phi_p = pi * r_p**gamma, r_p = (U_p - Umin)/(Umax - Umin)."""
    U = np.asarray(U, float)
    r = (U - U.min()) / (U.max() - U.min())
    return np.pi * r ** gamma


def hard_phases(U: np.ndarray, valid: np.ndarray | None = None) -> np.ndarray:
    """Single marked state (phi = pi at argmax of U over the admissible set, 0 elsewhere; Eq. 2)."""
    U = np.asarray(U, float)
    ph = np.zeros(len(U))
    ph[int(np.argmax(U if valid is None else np.where(valid, U, -np.inf)))] = np.pi
    return ph


def amplitude_search(phases: np.ndarray, K: int) -> np.ndarray:
    """K iterations of (R_s . O_phi) on the uniform state; returns the 16 probabilities."""
    n = len(phases)
    a = np.full(n, 1 / np.sqrt(n), dtype=complex)
    for _ in range(K):
        a = a * np.exp(1j * phases)   # phase oracle
        a = 2 * a.mean() - a          # diffusion: inversion about the mean
    return np.abs(a) ** 2


def grover_p(K, n: int = N):
    """Eq. (11): P_target(K) = sin^2((2K+1) alpha), alpha = arcsin(1/sqrt(N))."""
    alpha = np.arcsin(1 / np.sqrt(n))
    return np.sin((2 * np.asarray(K) + 1) * alpha) ** 2


def k_opt(n: int = N) -> int:
    return int(np.floor(np.pi * np.sqrt(n) / 4))


def candidate_set_seed42() -> np.ndarray:
    """16 x 5 uniform features, NumPy default_rng(42) (manuscript Sec. 5.2 'Independent re-run')."""
    return np.random.default_rng(42).random((N, 5))


def select(U: np.ndarray, mode: str = "soft", K: int | None = None,
           valid: np.ndarray | None = None, gamma: float = 6.0) -> int:
    """Return the selected candidate index (argmax of probability over valid indices)."""
    if mode == "argmax":
        p = np.asarray(U, float)
    else:
        ph = soft_phases(U, gamma) if mode == "soft" else hard_phases(U, valid)
        if K is None:
            K = 2 if mode == "soft" else k_opt(len(U))
        p = amplitude_search(ph, K)
    if valid is not None:
        p = np.where(valid, p, -np.inf)
    return int(np.argmax(p))
