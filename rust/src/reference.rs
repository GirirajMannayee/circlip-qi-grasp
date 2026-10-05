//! Loaders for the Python reference vectors (offline verification path of Fig. 13).
use crate::cost::GraspError;
use crate::{Features, N, NF};
use std::fs;

pub fn read_rows(path: &str) -> Result<Vec<Vec<f64>>, GraspError> {
    let txt = fs::read_to_string(path).map_err(|e| GraspError::Parse(format!("{path}: {e}")))?;
    txt.lines()
        .map(str::trim)
        .filter(|l| !l.is_empty() && !l.starts_with('#'))
        .map(|l| {
            l.split(',')
                .map(|t| {
                    t.trim()
                        .parse::<f64>()
                        .map_err(|e| GraspError::Parse(format!("{path}: '{t}': {e}")))
                })
                .collect()
        })
        .collect()
}
pub fn features_from_flat(v: &[f64]) -> Result<Features, GraspError> {
    if v.len() < N * NF {
        return Err(GraspError::Parse(format!(
            "need {} features, got {}",
            N * NF,
            v.len()
        )));
    }
    let mut f = [[0.0; NF]; N];
    for p in 0..N {
        for j in 0..NF {
            f[p][j] = v[p * NF + j];
        }
    }
    Ok(f)
}
/// Single 16×5 matrix: either 16 lines × 5 columns or one line × 80 columns.
pub fn read_features(path: &str) -> Result<Features, GraspError> {
    let rows = read_rows(path)?;
    let flat: Vec<f64> = rows.into_iter().flatten().collect();
    features_from_flat(&flat)
}
/// One record of `reference_vectors.csv`: 80 features | 16 P(hard,K=3) | 16 P(soft,K=2) | 16 P(soft,K=3) | idx argmax, hard3, soft2, soft3.
pub struct RefRecord {
    pub features: Features,
    pub p_hard3: [f64; N],
    pub p_soft2: [f64; N],
    pub p_soft3: [f64; N],
    pub idx: [usize; 4],
}
pub fn read_reference(path: &str) -> Result<Vec<RefRecord>, GraspError> {
    read_rows(path)?
        .into_iter()
        .map(|r| {
            if r.len() != 80 + 48 + 4 {
                return Err(GraspError::Parse(format!(
                    "expected 132 columns, got {}",
                    r.len()
                )));
            }
            let take = |o: usize| {
                let mut a = [0.0; N];
                a.copy_from_slice(&r[o..o + N]);
                a
            };
            Ok(RefRecord {
                features: features_from_flat(&r[..80])?,
                p_hard3: take(80),
                p_soft2: take(96),
                p_soft3: take(112),
                idx: [
                    r[128] as usize,
                    r[129] as usize,
                    r[130] as usize,
                    r[131] as usize,
                ],
            })
        })
        .collect()
}
