//! Bounded selection service (Fig. 13, layer L2): validation → utility → amplitude search → admissibility mask,
//! guarded by a latency watchdog that falls back to the best classical candidate (exhaustive argmax).
use crate::amplitude::{self, DEFAULT_GAMMA};
use crate::cost::{self, argmax_valid, GraspError};
use crate::{Features, N};
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Mode {
    /// Exhaustive argmax over admissible utilities (exact; the classical comparator).
    Argmax,
    /// Hard oracle marking the best admissible candidate; `k = None` ⇒ K_opt = 3.
    Hard { k: Option<usize> },
    /// Graded-phase oracle (Eq. 12); manuscript default K = 2, γ = 6.
    Soft { k: usize, gamma: f64 },
}
impl Mode {
    pub const SOFT_DEFAULT: Mode = Mode::Soft {
        k: 2,
        gamma: DEFAULT_GAMMA,
    };
    pub const HARD_DEFAULT: Mode = Mode::Hard { k: None };
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FallbackReason {
    WatchdogTimeout,
    NonFiniteAmplitudes,
}

#[derive(Debug, Clone)]
pub struct Request<'a> {
    pub features: &'a Features,
    /// Clearance ∧ reachability mask: 𝒜 (Eq. 6).
    pub valid: &'a [bool; N],
    pub mode: Mode,
    /// T_wd: maximum optimizer latency (None ⇒ unbounded).
    pub watchdog: Option<Duration>,
}

#[derive(Debug, Clone)]
pub struct Response {
    pub selected: usize,
    pub utility: f64,
    /// Probability of the selected candidate after the search (None for argmax / fallback).
    pub probability: Option<f64>,
    pub iterations: usize,
    pub elapsed_ns: u128,
    pub fallback: Option<FallbackReason>,
}

fn classical(u: &[f64; N], valid: &[bool; N]) -> Result<usize, GraspError> {
    argmax_valid(u, valid).ok_or(GraspError::NoAdmissibleCandidate)
}

/// Run one selection cycle. Loops are bounded (K ≤ a small constant) and nothing is heap-allocated.
pub fn select(req: &Request) -> Result<Response, GraspError> {
    let t0 = Instant::now();
    cost::validate(req.features)?;
    let u = cost::utilities(req.features);
    let best_classical = classical(&u, req.valid)?;

    let finish = |sel: usize, prob: Option<f64>, it: usize, fb: Option<FallbackReason>| Response {
        selected: sel,
        utility: u[sel],
        probability: prob,
        iterations: it,
        elapsed_ns: t0.elapsed().as_nanos(),
        fallback: fb,
    };

    let (phase, k) = match req.mode {
        Mode::Argmax => return Ok(finish(best_classical, None, 0, None)),
        Mode::Hard { k } => (
            amplitude::hard_phases(&u, req.valid).ok_or(GraspError::NoAdmissibleCandidate)?,
            k.unwrap_or_else(amplitude::k_opt),
        ),
        Mode::Soft { k, gamma } => (amplitude::soft_phases(&u, gamma), k),
    };

    let (mut re, mut im) = ([1.0 / (N as f64).sqrt(); N], [0.0_f64; N]);
    for it in 0..k {
        amplitude::step(&phase, &mut re, &mut im);
        if let Some(limit) = req.watchdog {
            if t0.elapsed() >= limit {
                return Ok(finish(
                    best_classical,
                    None,
                    it + 1,
                    Some(FallbackReason::WatchdogTimeout),
                ));
            }
        }
    }
    let p = amplitude::prob_of(&re, &im);
    if p.iter().any(|x| !x.is_finite()) {
        return Ok(finish(
            best_classical,
            None,
            k,
            Some(FallbackReason::NonFiniteAmplitudes),
        ));
    }
    let sel = argmax_valid(&p, req.valid).ok_or(GraspError::NoAdmissibleCandidate)?;
    Ok(finish(sel, Some(p[sel]), k, None))
}
