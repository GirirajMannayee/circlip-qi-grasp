"""PI force regulation (Sec. 3.4, Eq. 9) and seating tilt (Sec. 3.2, Eq. 3). Fig. 5b.

Plant (assumption A4): F_m = k_c * x_f, velocity-commanded finger dx_f/dt = u_F.
Closed loop F_d -> F_m:  (2 zeta wn s + wn^2) / (s^2 + 2 zeta wn s + wn^2),
wn = sqrt(k_c K_I), zeta = k_c K_P / (2 wn).
"""
from __future__ import annotations
import numpy as np
from scipy import signal


def closed_loop(zeta: float, wn: float = 1.0) -> signal.TransferFunction:
    return signal.TransferFunction([2 * zeta * wn, wn ** 2], [1, 2 * zeta * wn, wn ** 2])


def step_response(zeta: float, wn: float = 1.0, t_end: float = 12.0, n: int = 1200):
    t = np.linspace(0, t_end, n)
    t, y = signal.step(closed_loop(zeta, wn), T=t)
    return t, y


def overshoot_pct(zeta: float) -> float:
    _, y = step_response(zeta, t_end=40.0, n=8000)
    return float(max(0.0, (y.max() - 1.0) * 100))


def gains_from_wn_zeta(kc: float, wn: float, zeta: float) -> tuple[float, float]:
    """K_I = wn^2 / k_c, K_P = 2 zeta wn / k_c  (inverse of the relations above)."""
    return 2 * zeta * wn / kc, wn ** 2 / kc


def simulate_pi(kc=1.0, wn=1.0, zeta=1.0, Fd=14.0, i_max=None, f_max=20.0, dt=1e-3, t_end=12.0):
    """Discrete PI with integrator clamp and hard force ceiling; returns (t, F_m, u)."""
    Kp, Ki = gains_from_wn_zeta(kc, wn, zeta)
    n = int(t_end / dt); x = I = 0.0
    t = np.arange(n) * dt; F = np.zeros(n); U = np.zeros(n)
    i_max = Fd * 2 if i_max is None else i_max
    for k in range(n):
        Fm = kc * x; F[k] = Fm
        e = Fd - Fm
        I = float(np.clip(I + e * dt, -i_max / max(Ki, 1e-12), i_max / max(Ki, 1e-12)))  # anti-windup clamp
        u = Kp * e + Ki * I; U[k] = u
        if Fm >= f_max and u > 0:                     # independent supervisor: ceiling
            u = 0.0
        x += u * dt
    return t, F, U


def tilt_deg(r_mm: float, F_N: float, k_eff_Nm_per_rad: float) -> float:
    """Eq. (3) with r perpendicular to F: theta ~ |M|/k_eff, small-angle (A3)."""
    M = (r_mm * 1e-3) * F_N
    return float(np.degrees(M / k_eff_Nm_per_rad))
