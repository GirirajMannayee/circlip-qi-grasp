//! Quantum-inspired amplitude search (Eq. 10–12): uniform state → [phase oracle → inversion about the mean]×K.
//! Allocation-free; the 16 complex amplitudes live in two stack arrays.
use crate::cost::argmax_valid;
use crate::{GAMMA, N};
use std::f64::consts::PI;

/// Eq. (12): φ_p = π · r_p^γ with r_p = (U_p − U_min)/(U_max − U_min). Constant U ⇒ all phases 0 (no NaN).
pub fn soft_phases(u: &[f64; N], gamma: f64) -> [f64; N] {
    let (mut lo, mut hi) = (f64::INFINITY, f64::NEG_INFINITY);
    for &x in u {
        lo = lo.min(x);
        hi = hi.max(x);
    }
    let span = hi - lo;
    let mut ph = [0.0; N];
    if span > 0.0 {
        for i in 0..N {
            ph[i] = PI * ((u[i] - lo) / span).powf(gamma);
        }
    }
    ph
}

/// Single marked state: φ = π at the best *admissible* candidate (Eq. 2), 0 elsewhere.
pub fn hard_phases(u: &[f64; N], valid: &[bool; N]) -> Option<[f64; N]> {
    let b = argmax_valid(u, valid)?;
    let mut ph = [0.0; N];
    ph[b] = PI;
    Some(ph)
}

/// Run K iterations; returns amplitudes (re, im).
#[inline]
pub fn evolve(phase: &[f64; N], k: usize) -> ([f64; N], [f64; N]) {
    let (mut re, mut im) = ([1.0 / (N as f64).sqrt(); N], [0.0_f64; N]);
    for _ in 0..k {
        step(phase, &mut re, &mut im);
    }
    (re, im)
}

/// One iteration R_s · O_φ.
#[inline]
pub fn step(phase: &[f64; N], re: &mut [f64; N], im: &mut [f64; N]) {
    for i in 0..N {
        // phase oracle O_φ
        let (s, c) = phase[i].sin_cos();
        let (r, m) = (re[i], im[i]);
        re[i] = r * c - m * s;
        im[i] = r * s + m * c;
    }
    let (mut mr, mut mi) = (0.0, 0.0); // diffusion R_s = 2|s><s| − I
    for i in 0..N {
        mr += re[i];
        mi += im[i];
    }
    mr /= N as f64;
    mi /= N as f64;
    for i in 0..N {
        re[i] = 2.0 * mr - re[i];
        im[i] = 2.0 * mi - im[i];
    }
}

/// Candidate probabilities |a_p|² after K iterations.
pub fn probabilities(phase: &[f64; N], k: usize) -> [f64; N] {
    let (re, im) = evolve(phase, k);
    let mut p = [0.0; N];
    for i in 0..N {
        p[i] = re[i] * re[i] + im[i] * im[i];
    }
    p
}

#[inline]
pub fn prob_of(re: &[f64; N], im: &[f64; N]) -> [f64; N] {
    let mut p = [0.0; N];
    for i in 0..N {
        p[i] = re[i] * re[i] + im[i] * im[i];
    }
    p
}

/// Appendix B.3 `select_grasp`: bounded, allocation-free; returns the most probable *valid* candidate.
pub fn select_grasp(phase: &[f64; N], k: usize, valid: &[bool; N]) -> Option<usize> {
    argmax_valid(&probabilities(phase, k), valid)
}

/// Eq. (11): P_target(K) = sin²((2K+1)α), α = arcsin(1/√N).
pub fn grover_p(k: usize) -> f64 {
    let a = (1.0 / (N as f64).sqrt()).asin();
    ((2 * k + 1) as f64 * a).sin().powi(2)
}

/// K_opt = ⌊π√N/4⌋ (= 3 for N = 16).
pub fn k_opt() -> usize {
    (PI * (N as f64).sqrt() / 4.0).floor() as usize
}

/// Default soft-oracle exponent (γ = 6) re-exported for convenience.
pub const DEFAULT_GAMMA: f64 = GAMMA;
