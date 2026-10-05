//! Eq. (9) PI force law with integrator clamp and an independent force ceiling (Sec. 3.4).
//! Plant (assumption A4): F_m = k_c·x_f, velocity-commanded finger dx_f/dt = u_F.
#[derive(Debug, Clone, Copy)]
pub struct Pi {
    pub kp: f64,
    pub ki: f64,
    pub i_clamp: f64,
    pub f_max: f64,
    integ: f64,
}
impl Pi {
    pub fn new(kp: f64, ki: f64, i_clamp: f64, f_max: f64) -> Self {
        Pi {
            kp,
            ki,
            i_clamp,
            f_max,
            integ: 0.0,
        }
    }
    /// Gains from (k_c, ω_n, ζ): K_P = 2ζω_n/k_c, K_I = ω_n²/k_c  (inverse of ω_n = √(k_c K_I), ζ = k_c K_P/(2ω_n)).
    pub fn from_wn_zeta(kc: f64, wn: f64, zeta: f64, i_clamp: f64, f_max: f64) -> Self {
        Pi::new(2.0 * zeta * wn / kc, wn * wn / kc, i_clamp, f_max)
    }
    /// One control update. Returns the finger-velocity command u_F (zero if the ceiling is exceeded).
    pub fn update(&mut self, fd: f64, fm: f64, dt: f64) -> f64 {
        let e = fd - fm;
        self.integ = (self.integ + e * dt).clamp(-self.i_clamp, self.i_clamp); // anti-windup
        let u = self.kp * e + self.ki * self.integ;
        if fm >= self.f_max && u > 0.0 {
            0.0
        } else {
            u
        } // safety-supervisor ceiling
    }
}
/// Normalised step response F_m/F_d of the closed loop (k_c = ω_n = 1). Returns (t, y).
pub fn step_response(zeta: f64, t_end: f64, dt: f64) -> Vec<(f64, f64)> {
    let mut pi = Pi::from_wn_zeta(1.0, 1.0, zeta, f64::INFINITY, f64::INFINITY);
    let (mut x, mut out) = (0.0_f64, Vec::with_capacity((t_end / dt) as usize));
    let n = (t_end / dt) as usize;
    for k in 0..n {
        let t = k as f64 * dt;
        out.push((t, x));
        // explicit Euler; dt = 1e-4 keeps the overshoot error well below 0.1 percentage point
        let u1 = pi.update(1.0, x, dt);
        x += u1 * dt;
    }
    out
}
/// Peak overshoot in percent of the setpoint.
pub fn overshoot_pct(zeta: f64) -> f64 {
    let y = step_response(zeta, 40.0, 1e-4);
    (y.iter().map(|p| p.1).fold(f64::MIN, f64::max) - 1.0).max(0.0) * 100.0
}
