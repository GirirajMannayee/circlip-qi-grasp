use qi_grasp::amplitude::*;
use qi_grasp::cost::*;
use qi_grasp::reference::{read_features, read_reference};
use qi_grasp::select::{select, FallbackReason, Mode, Request};
use qi_grasp::{force, montecarlo, tilt, N, NF, WEIGHTS};
use std::time::Duration;

fn data(p: &str) -> String {
    format!("{}/../data/reference/{p}", env!("CARGO_MANIFEST_DIR"))
}
fn seed42() -> qi_grasp::Features {
    read_features(&data("seed42_features.csv")).unwrap()
}
const ALL: [bool; N] = [true; N];

// ---- Eq. (1)-(2) ---------------------------------------------------------------------------------------
#[test]
fn weights_sum_to_one() {
    assert!((WEIGHTS.iter().sum::<f64>() - 1.0).abs() < 1e-15);
}
#[test]
fn seed42_best_candidate_is_5_with_u_0725() {
    let u = utilities(&seed42());
    let b = argmax_valid(&u, &ALL).unwrap();
    assert_eq!(b, 5);
    assert!((u[5] - 0.725).abs() < 5e-4, "U = {}", u[5]);
}
#[test]
fn utility_is_monotone_in_every_feature() {
    let base = [[0.4; NF]; N];
    for j in 0..NF {
        let mut worse = base;
        worse[3][j] = 0.9; // higher normalized penalty ⇒ lower utility
        assert!(utilities(&worse)[3] < utilities(&base)[3]);
    }
}
#[test]
fn nan_inf_and_out_of_range_features_are_rejected() {
    for bad in [f64::NAN, f64::INFINITY, -0.1, 1.1] {
        let mut f = seed42();
        f[7][2] = bad;
        assert!(matches!(
            validate(&f),
            Err(GraspError::InvalidFeature {
                candidate: 7,
                feature: 2,
                ..
            })
        ));
        assert!(select(&Request {
            features: &f,
            valid: &ALL,
            mode: Mode::SOFT_DEFAULT,
            watchdog: None
        })
        .is_err());
    }
}

// ---- Eq. (10)-(12), Proposition 1 -------------------------------------------------------------------------
#[test]
fn hard_oracle_matches_grover_law_k0_to_6() {
    let u = utilities(&seed42());
    let ph = hard_phases(&u, &ALL).unwrap();
    for k in 0..=6 {
        assert!(
            (probabilities(&ph, k)[5] - grover_p(k)).abs() < 1e-12,
            "K={k}"
        );
    }
}
#[test]
fn proposition_1_values() {
    let want = [0.062, 0.473, 0.908, 0.961, 0.582, 0.125, 0.020];
    for (k, w) in want.iter().enumerate() {
        assert!((grover_p(k) - w).abs() < 6e-4, "K={k}: {}", grover_p(k));
    }
    assert_eq!(k_opt(), 3);
}
#[test]
fn probabilities_are_normalised() {
    let u = utilities(&seed42());
    for ph in [hard_phases(&u, &ALL).unwrap(), soft_phases(&u, 6.0)] {
        for k in 0..8 {
            assert!((probabilities(&ph, k).iter().sum::<f64>() - 1.0).abs() < 1e-12);
        }
    }
}
#[test]
fn soft_oracle_peaks_at_k2_on_seed42() {
    let u = utilities(&seed42());
    let ph = soft_phases(&u, 6.0);
    let p2 = probabilities(&ph, 2)[5];
    let p3 = probabilities(&ph, 3)[5];
    assert!((p2 - 0.506).abs() < 1e-3, "{p2}");
    assert!((p3 - 0.280).abs() < 1e-3, "{p3}");
    assert!(p2 > p3);
}
#[test]
fn constant_utilities_do_not_produce_nan() {
    let ph = soft_phases(&[0.5; N], 6.0);
    assert!(ph.iter().all(|x| *x == 0.0));
    assert!(probabilities(&ph, 3).iter().all(|p| p.is_finite()));
}
#[test]
fn select_grasp_appendix_b3_matches_service() {
    let u = utilities(&seed42());
    let ph = soft_phases(&u, 6.0);
    assert_eq!(select_grasp(&ph, 2, &ALL), Some(5));
}

// ---- selection service --------------------------------------------------------------------------------------
fn req<'a>(f: &'a qi_grasp::Features, v: &'a [bool; N], m: Mode) -> Request<'a> {
    Request {
        features: f,
        valid: v,
        mode: m,
        watchdog: None,
    }
}
#[test]
fn all_modes_agree_on_seed42() {
    let f = seed42();
    for m in [
        Mode::Argmax,
        Mode::HARD_DEFAULT,
        Mode::SOFT_DEFAULT,
        Mode::Soft { k: 3, gamma: 6.0 },
    ] {
        assert_eq!(select(&req(&f, &ALL, m)).unwrap().selected, 5);
    }
}
#[test]
fn selection_is_deterministic() {
    let f = seed42();
    let a = select(&req(&f, &ALL, Mode::SOFT_DEFAULT)).unwrap();
    let b = select(&req(&f, &ALL, Mode::SOFT_DEFAULT)).unwrap();
    assert_eq!(
        (a.selected, a.probability, a.iterations),
        (b.selected, b.probability, b.iterations)
    );
}
#[test]
fn collision_mask_excludes_inadmissible_candidates() {
    let f = seed42();
    let mut v = ALL;
    v[5] = false;
    let u = utilities(&f);
    let want = argmax_valid(&u, &v).unwrap();
    assert_ne!(want, 5);
    for m in [Mode::Argmax, Mode::HARD_DEFAULT, Mode::SOFT_DEFAULT] {
        let r = select(&req(&f, &v, m)).unwrap();
        assert!(v[r.selected]);
    }
    assert_eq!(
        select(&req(&f, &v, Mode::HARD_DEFAULT)).unwrap().selected,
        want,
        "hard oracle marks the best ADMISSIBLE candidate"
    );
}
#[test]
fn empty_admissible_set_is_an_error() {
    let f = seed42();
    assert_eq!(
        select(&req(&f, &[false; N], Mode::SOFT_DEFAULT)).unwrap_err(),
        GraspError::NoAdmissibleCandidate
    );
}
#[test]
fn watchdog_timeout_falls_back_to_classical_argmax() {
    let f = seed42();
    let r = select(&Request {
        features: &f,
        valid: &ALL,
        mode: Mode::Soft { k: 3, gamma: 6.0 },
        watchdog: Some(Duration::ZERO),
    })
    .unwrap();
    assert_eq!(r.fallback, Some(FallbackReason::WatchdogTimeout));
    assert_eq!(r.selected, 5);
    assert!(r.probability.is_none());
}
#[test]
fn generous_watchdog_does_not_trigger() {
    let f = seed42();
    let r = select(&Request {
        features: &f,
        valid: &ALL,
        mode: Mode::SOFT_DEFAULT,
        watchdog: Some(Duration::from_secs(1)),
    })
    .unwrap();
    assert!(r.fallback.is_none());
}

// ---- cross-language verification (Gate 1) ---------------------------------------------------------------------
#[test]
fn matches_python_reference_vectors() {
    let recs = read_reference(&data("reference_vectors.csv")).unwrap();
    assert_eq!(recs.len(), 500);
    let mut maxd = 0.0f64;
    for r in &recs {
        let u = utilities(&r.features);
        let ps = soft_phases(&u, 6.0);
        for (got, want) in [
            (probabilities(&hard_phases(&u, &ALL).unwrap(), 3), r.p_hard3),
            (probabilities(&ps, 2), r.p_soft2),
            (probabilities(&ps, 3), r.p_soft3),
        ] {
            for i in 0..N {
                maxd = maxd.max((got[i] - want[i]).abs());
            }
        }
        for (m, mode) in [
            Mode::Argmax,
            Mode::HARD_DEFAULT,
            Mode::SOFT_DEFAULT,
            Mode::Soft { k: 3, gamma: 6.0 },
        ]
        .into_iter()
        .enumerate()
        {
            assert_eq!(
                select(&req(&r.features, &ALL, mode)).unwrap().selected,
                r.idx[m]
            );
        }
    }
    assert!(maxd < 1e-12, "max |ΔP| = {maxd:e}");
}

// ---- Sec. 5.3 Monte-Carlo ---------------------------------------------------------------------------------------
#[test]
fn montecarlo_reproduces_ordering_of_table_15() {
    let r = montecarlo::run(2000, 43);
    assert_eq!(r[0].top1, 100.0);
    assert_eq!(r[3].top1, 100.0); // argmax and hard K=3 exact
    assert!(r[4].top1 > 99.0); // soft K=2
    assert!(r[5].top1 > 92.0 && r[5].top1 < 97.0); // soft K=3 ≈ 95 %
    assert!(r[1].top1 < 30.0 && r[1].top1 > 18.0); // greedy ≈ 24 %
    assert!(r[2].top1 > 44.0 && r[2].top1 < 56.0); // random(8) ≈ 48 %
    assert!(r[1].mean_regret > r[2].mean_regret && r[2].mean_regret > r[5].mean_regret);
    assert_eq!(r[2].evals, 8);
}
#[test]
fn montecarlo_is_deterministic() {
    let (a, b) = (montecarlo::run(300, 5), montecarlo::run(300, 5));
    for (x, y) in a.iter().zip(b.iter()) {
        assert_eq!(x.top1, y.top1);
        assert_eq!(x.mean_regret, y.mean_regret);
    }
}

// ---- Eq. (3), (9), Sec. 3.4 --------------------------------------------------------------------------------------
#[test]
fn force_overshoot_matches_manuscript() {
    for (z, want) in [(0.5, 30.0), (0.7, 21.0), (1.0, 14.0), (1.5, 8.0)] {
        let o = force::overshoot_pct(z);
        assert!((o - want).abs() < 1.0, "zeta={z}: {o}");
    }
}
#[test]
fn pi_integrator_is_clamped_and_ceiling_enforced() {
    let mut pi = force::Pi::new(1.0, 1.0, 0.5, 20.0);
    for _ in 0..10_000 {
        pi.update(14.0, 0.0, 0.01);
    } // saturate the integrator
    assert!((pi.update(14.0, 0.0, 0.01) - (14.0 + 0.5)).abs() < 1e-9); // kp*e + ki*clamp
    assert_eq!(
        force::Pi::new(1.0, 1.0, 1.0, 20.0).update(30.0, 21.0, 0.01),
        0.0
    ); // above F_max ⇒ no further closing
}
#[test]
fn tilt_small_angle_and_cross_product() {
    assert_eq!(
        tilt::cross([1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
        [0.0, 0.0, 1.0]
    );
    let th = tilt::tilt_rad([0.01, 0.0, 0.0], [0.0, 5.0, 0.0], 0.5); // M = 0.05 N·m, k = 0.5 ⇒ 0.1 rad
    assert!((th - 0.1).abs() < 1e-12);
    assert!(tilt::small_angle_error(10f64.to_radians()) < 0.006); // ≈ 0.5 % at 10° (A3)
}
