#![allow(clippy::needless_range_loop)]
//! # qi_grasp — QIO-Rust core
//!
//! Rust implementation of the layer-L2 optimizer of *Quantum-Inspired Multi-Objective Grasp
//! Optimization for Vision–Force Adaptive Circlip-to-Sleeve Assembly* (Sec. 4.5, Fig. 13, App. B.3).
//!
//! * [`cost`]       — Eq. (1)–(2): five-term cost and utility, request validation.
//! * [`amplitude`]  — Eq. (10)–(12): amplitude search (hard / graded-phase oracle), Grover law (11).
//! * [`select`]     — bounded selection service with latency watchdog and classical fallback.
//! * [`force`]      — Eq. (9): PI force loop with anti-windup; closed-loop step response (Fig. 5b).
//! * [`tilt`]       — Eq. (3): seating moment and tilt.
//! * [`montecarlo`] — Sec. 5.3 candidate-selection study (Table 15) with an in-crate PRNG.
//! * [`reference`]  — loaders for Python-exported reference vectors (offline verification path).
//! * [`stats`]      — latency percentile helper (median / p95 / p99.9).
//!
//! No quantum library is used; the 16 amplitudes are plain `f64` arrays. The crate has no dependencies.
//! **Evidence status:** compiling and unit-testing here closes the *software* part of Gate 1;
//! hypothesis H5 (edge-hardware latency) still requires profiling on the target device.

pub mod amplitude;
pub mod cost;
pub mod force;
pub mod montecarlo;
pub mod reference;
pub mod rng;
pub mod select;
pub mod stats;
pub mod tilt;

/// Number of candidate contacts (n = 4 qubits).
pub const N: usize = 16;
/// Number of normalized features per candidate: (E_p, E_theta, D_e, F_n, S_d).
pub const NF: usize = 5;
/// Weights of Eq. (1).
pub const WEIGHTS: [f64; NF] = [0.30, 0.25, 0.20, 0.15, 0.10];
/// Graded-phase exponent of Eq. (12).
pub const GAMMA: f64 = 6.0;

/// 16 × 5 feature matrix (row = candidate).
pub type Features = [[f64; NF]; N];
