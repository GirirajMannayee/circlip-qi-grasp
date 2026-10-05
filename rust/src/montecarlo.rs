//! Sec. 5.3 candidate-selection study (Table 15): exhaustive argmax, position-only greedy, random subset (8 evals),
//! QI hard K = 3, QI soft K = 2 and K = 3 on synthetic 16 × 5 uniform sets.
use crate::amplitude::{hard_phases, probabilities, soft_phases};
use crate::cost::{argmax_valid, utilities};
use crate::rng::Rng;
use crate::stats::percentile;
use crate::{Features, GAMMA, N, NF};

pub const METHODS: [&str; 6] = [
    "Exhaustive argmax",
    "Greedy (position only)",
    "Random subset (8 evals)",
    "QI hard K = 3",
    "QI soft K = 2",
    "QI soft K = 3",
];
pub const EVALS: [usize; 6] = [16, 16, 8, 16, 16, 16];
#[derive(Debug, Clone)]
pub struct Row {
    pub method: &'static str,
    pub top1: f64,
    pub top3: f64,
    pub mean_regret: f64,
    pub p95_regret: f64,
    pub evals: usize,
}

pub fn random_set(rng: &mut Rng) -> Features {
    let mut f = [[0.0; NF]; N];
    for p in 0..N {
        for j in 0..NF {
            f[p][j] = rng.next_f64();
        }
    }
    f
}
pub fn run(n_sets: usize, seed: u64) -> Vec<Row> {
    let mut rng = Rng::new(seed);
    let all = [true; N];
    let (mut hit1, mut hit3) = ([0usize; 6], [0usize; 6]);
    let mut regret: Vec<Vec<f64>> = (0..6).map(|_| Vec::with_capacity(n_sets)).collect();
    for _ in 0..n_sets {
        let f = random_set(&mut rng);
        let u = utilities(&f);
        let best = u.iter().cloned().fold(f64::MIN, f64::max);
        let mut s = u.to_vec();
        s.sort_by(|a, b| a.total_cmp(b));
        let third = s[N - 3];
        let mut sel = [0usize; 6];
        sel[0] = argmax_valid(&u, &all).unwrap();
        sel[1] = (0..N).fold(0, |b, i| if f[i][0] < f[b][0] { i } else { b });
        let sub: [usize; 8] = rng.sample_distinct::<8>(N);
        sel[2] = sub
            .iter()
            .cloned()
            .fold(sub[0], |b, i| if u[i] > u[b] { i } else { b });
        sel[3] = argmax_valid(&probabilities(&hard_phases(&u, &all).unwrap(), 3), &all).unwrap();
        sel[4] = argmax_valid(&probabilities(&soft_phases(&u, GAMMA), 2), &all).unwrap();
        sel[5] = argmax_valid(&probabilities(&soft_phases(&u, GAMMA), 3), &all).unwrap();
        for m in 0..6 {
            let us = u[sel[m]];
            if us >= best - 1e-12 {
                hit1[m] += 1;
            }
            if us >= third - 1e-12 {
                hit3[m] += 1;
            }
            regret[m].push(best - us);
        }
    }
    (0..6)
        .map(|m| {
            regret[m].sort_by(|a, b| a.total_cmp(b));
            Row {
                method: METHODS[m],
                top1: 100.0 * hit1[m] as f64 / n_sets as f64,
                top3: 100.0 * hit3[m] as f64 / n_sets as f64,
                mean_regret: regret[m].iter().sum::<f64>() / n_sets as f64,
                p95_regret: percentile(&regret[m], 95.0),
                evals: EVALS[m],
            }
        })
        .collect()
}
