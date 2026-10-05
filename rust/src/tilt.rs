//! Eq. (3): seating moment M = r × F and small-angle tilt θ ≈ |M| / k_eff (assumption A3: |θ| ≲ 10°).
pub type V3 = [f64; 3];
pub fn cross(a: V3, b: V3) -> V3 {
    [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]
}
pub fn norm(a: V3) -> f64 {
    (a[0] * a[0] + a[1] * a[1] + a[2] * a[2]).sqrt()
}
/// `r` in metres, `f` in newtons, `k_eff` in N·m/rad. Returns tilt in radians.
pub fn tilt_rad(r: V3, f: V3, k_eff: f64) -> f64 {
    norm(cross(r, f)) / k_eff
}
pub fn tilt_deg(r: V3, f: V3, k_eff: f64) -> f64 {
    tilt_rad(r, f, k_eff).to_degrees()
}
/// Relative error of sin θ ≈ θ — the manuscript quotes ≈ 0.5 % at 10°.
pub fn small_angle_error(theta_rad: f64) -> f64 {
    (theta_rad - theta_rad.sin()) / theta_rad.sin()
}
