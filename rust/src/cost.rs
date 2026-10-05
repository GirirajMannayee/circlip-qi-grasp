//! Eq. (1)–(2): weighted cost J(p), utility U(p) = 1 − J(p), and input validation.
use crate::{Features, N, NF, WEIGHTS};
use std::fmt;

/// Errors a controller must be able to reject before motion (Sec. 4.5).
#[derive(Debug, Clone, PartialEq)]
pub enum GraspError {
    /// A feature is NaN/∞ or outside [0, 1].
    InvalidFeature {
        candidate: usize,
        feature: usize,
        value: f64,
    },
    /// Clearance + reachability mask excludes every candidate (𝒜 = ∅).
    NoAdmissibleCandidate,
    /// Malformed text input (reference / CLI loaders).
    Parse(String),
}
impl fmt::Display for GraspError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            GraspError::InvalidFeature { candidate, feature, value } =>
                write!(f, "invalid feature {value} at candidate {candidate}, feature {feature} (need finite value in [0,1])"),
            GraspError::NoAdmissibleCandidate => write!(f, "no admissible candidate (clearance/reachability mask is empty)"),
            GraspError::Parse(s) => write!(f, "parse error: {s}"),
        }
    }
}
impl std::error::Error for GraspError {}

/// Reject NaN, ±∞ and values outside [0, 1] (incomplete-sensor handling).
pub fn validate(features: &Features) -> Result<(), GraspError> {
    for (p, row) in features.iter().enumerate() {
        for (j, &v) in row.iter().enumerate() {
            if !v.is_finite() || !(0.0..=1.0).contains(&v) {
                return Err(GraspError::InvalidFeature {
                    candidate: p,
                    feature: j,
                    value: v,
                });
            }
        }
    }
    Ok(())
}

/// Eq. (1): J(p) = 0.30 E'p + 0.25 E'θ + 0.20 D'e + 0.15 F'n + 0.10 S'd.
#[inline]
pub fn cost_of(row: &[f64; NF]) -> f64 {
    let mut j = 0.0;
    for k in 0..NF {
        j += WEIGHTS[k] * row[k];
    }
    j
}

/// Eq. (2): U(p) = 1 − J(p) for all 16 candidates.
pub fn utilities(features: &Features) -> [f64; N] {
    let mut u = [0.0; N];
    for p in 0..N {
        u[p] = 1.0 - cost_of(&features[p]);
    }
    u
}

/// First index of the maximum over the admissible set (ties → lowest index, as NumPy `argmax`).
pub fn argmax_valid(values: &[f64; N], valid: &[bool; N]) -> Option<usize> {
    let mut best: Option<usize> = None;
    for i in 0..N {
        if !valid[i] {
            continue;
        }
        match best {
            None => best = Some(i),
            Some(b) if values[i] > values[b] => best = Some(i),
            _ => {}
        }
    }
    best
}
