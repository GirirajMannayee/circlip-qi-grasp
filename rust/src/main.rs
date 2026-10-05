#![allow(clippy::needless_range_loop)]
//! `qi-grasp` command-line interface (offline verification, Monte-Carlo and latency profiling).
use qi_grasp::amplitude::{grover_p, hard_phases, k_opt, probabilities};
use qi_grasp::cost::{utilities, GraspError};
use qi_grasp::reference::{read_features, read_reference};
use qi_grasp::select::{select, Mode, Request};
use qi_grasp::{force, montecarlo, stats, Features, N};
use std::time::Duration;

const USAGE: &str = "qi-grasp <command> [options]
commands:
  demo [--features FILE]                         utilities, probabilities K=0..6, selection under every mode
  select --features FILE [--mode argmax|hard|soft] [--k K] [--gamma G] [--valid 16-bit-mask] [--watchdog-us T]
  montecarlo [--sets 2000] [--seed 43]           Table 15 style comparison (in-crate PRNG)
  bench [--features FILE] [--calls 100000] [--mode ...] [--k K] [--watchdog-us T]   latency median/p95/p99.9 + fallback rate
  verify --ref reference_vectors.csv [--tol 1e-12]   compare with the Python reference (Gate 1 cross-check)
  step-response                                   overshoot for zeta = 0.5, 0.7, 1.0, 1.5 (Fig. 5b)";

fn arg<'a>(a: &'a [String], key: &str) -> Option<&'a str> {
    a.iter()
        .position(|x| x == key)
        .and_then(|i| a.get(i + 1))
        .map(|s| s.as_str())
}
fn parse<T: std::str::FromStr>(a: &[String], key: &str, d: T) -> T {
    arg(a, key).and_then(|s| s.parse().ok()).unwrap_or(d)
}
fn mode_from(a: &[String]) -> Mode {
    let k: Option<usize> = arg(a, "--k").and_then(|s| s.parse().ok());
    match arg(a, "--mode").unwrap_or("soft") {
        "argmax" => Mode::Argmax,
        "hard" => Mode::Hard { k },
        _ => Mode::Soft {
            k: k.unwrap_or(2),
            gamma: parse(a, "--gamma", qi_grasp::GAMMA),
        },
    }
}
fn mask_from(a: &[String]) -> [bool; N] {
    let mut m = [true; N];
    if let Some(s) = arg(a, "--valid") {
        for (i, c) in s.chars().take(N).enumerate() {
            m[i] = c == '1';
        }
    }
    m
}
fn load(a: &[String]) -> Result<Features, GraspError> {
    match arg(a, "--features") {
        Some(p) => read_features(p),
        None => read_features("data/reference/seed42_features.csv")
            .or_else(|_| read_features("../data/reference/seed42_features.csv")),
    }
}

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    let code = match run(&a) {
        Ok(()) => 0,
        Err(e) => {
            eprintln!("error: {e}");
            2
        }
    };
    std::process::exit(code);
}

fn run(a: &[String]) -> Result<(), GraspError> {
    match a.first().map(|s| s.as_str()) {
        Some("demo") => {
            let f = load(a)?;
            let u = utilities(&f);
            let all = [true; N];
            println!("utilities:");
            for p in 0..N {
                println!("  p={p:2} ({p:04b})  U={:.4}", u[p]);
            }
            let ph = hard_phases(&u, &all).ok_or(GraspError::NoAdmissibleCandidate)?;
            println!(
                "\nhard oracle: P(best) per iteration vs Grover law (K_opt = {})",
                k_opt()
            );
            let best = u
                .iter()
                .enumerate()
                .fold(0, |b, (i, &x)| if x > u[b] { i } else { b });
            for k in 0..=6 {
                println!(
                    "  K={k}  P={:.4}  Grover={:.4}",
                    probabilities(&ph, k)[best],
                    grover_p(k)
                );
            }
            for (name, mode) in [
                ("argmax", Mode::Argmax),
                ("hard K=3", Mode::HARD_DEFAULT),
                ("soft K=2", Mode::SOFT_DEFAULT),
                ("soft K=3", Mode::Soft { k: 3, gamma: 6.0 }),
            ] {
                let r = select(&Request {
                    features: &f,
                    valid: &all,
                    mode,
                    watchdog: None,
                })?;
                println!(
                    "{name:9} -> p={} U={:.4} prob={:?} iters={} {}ns",
                    r.selected,
                    r.utility,
                    r.probability.map(|x| (x * 1e4).round() / 1e4),
                    r.iterations,
                    r.elapsed_ns
                );
            }
            Ok(())
        }
        Some("select") => {
            let f = load(a)?;
            let valid = mask_from(a);
            let wd = arg(a, "--watchdog-us")
                .and_then(|s| s.parse().ok())
                .map(Duration::from_micros);
            let r = select(&Request {
                features: &f,
                valid: &valid,
                mode: mode_from(a),
                watchdog: wd,
            })?;
            println!("selected={} utility={:.6} probability={} iterations={} elapsed_ns={} fallback={:?}",
                     r.selected, r.utility, r.probability.map_or("-".into(), |p| format!("{p:.6}")), r.iterations, r.elapsed_ns, r.fallback);
            Ok(())
        }
        Some("montecarlo") => {
            let rows = montecarlo::run(parse(a, "--sets", 2000usize), parse(a, "--seed", 43u64));
            println!(
                "{:<26}{:>9}{:>9}{:>13}{:>16}{:>7}",
                "Method", "Top-1 %", "Top-3 %", "Mean regret", "95th-pct regret", "Evals"
            );
            for r in rows {
                println!(
                    "{:<26}{:>9.1}{:>9.1}{:>13.4}{:>16.4}{:>7}",
                    r.method, r.top1, r.top3, r.mean_regret, r.p95_regret, r.evals
                );
            }
            Ok(())
        }
        Some("bench") => {
            let f = load(a)?;
            let valid = mask_from(a);
            let calls = parse(a, "--calls", 100_000usize);
            let mode = mode_from(a);
            let wd = arg(a, "--watchdog-us")
                .and_then(|s| s.parse().ok())
                .map(Duration::from_micros);
            let req = Request {
                features: &f,
                valid: &valid,
                mode,
                watchdog: wd,
            };
            for _ in 0..1000 {
                std::hint::black_box(select(&req)?);
            } // warm-up
            let (mut ns, mut fb) = (Vec::with_capacity(calls), 0usize);
            for _ in 0..calls {
                let r = select(std::hint::black_box(&req))?;
                if r.fallback.is_some() {
                    fb += 1;
                }
                ns.push(r.elapsed_ns);
            }
            let s = stats::latency_summary(&mut ns);
            println!("mode={mode:?} calls={} median={:.3}us p95={:.3}us p99.9={:.3}us max={:.3}us mean={:.3}us fallback_rate={:.4}%",
                     s.n, s.median_us, s.p95_us, s.p999_us, s.max_us, s.mean_us, 100.0 * fb as f64 / calls as f64);
            println!("NOTE: measured on this machine only; hypothesis H5 requires the same run on the target edge hardware.");
            Ok(())
        }
        Some("verify") => {
            let path = arg(a, "--ref").ok_or_else(|| GraspError::Parse("--ref required".into()))?;
            let tol: f64 = parse(a, "--tol", 1e-12);
            let recs = read_reference(path)?;
            let all = [true; N];
            let (mut maxd, mut idx_bad) = (0.0_f64, 0usize);
            for r in &recs {
                let u = utilities(&r.features);
                let ph_h = hard_phases(&u, &all).unwrap();
                let ph_s = qi_grasp::amplitude::soft_phases(&u, 6.0);
                for (got, want) in [
                    (probabilities(&ph_h, 3), r.p_hard3),
                    (probabilities(&ph_s, 2), r.p_soft2),
                    (probabilities(&ph_s, 3), r.p_soft3),
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
                    if select(&Request {
                        features: &r.features,
                        valid: &all,
                        mode,
                        watchdog: None,
                    })?
                    .selected
                        != r.idx[m]
                    {
                        idx_bad += 1;
                    }
                }
            }
            println!(
                "records={} max|ΔP|={:.3e} (tol {:.0e}) selection mismatches={}",
                recs.len(),
                maxd,
                tol,
                idx_bad
            );
            if maxd > tol || idx_bad > 0 {
                return Err(GraspError::Parse(
                    "Rust output does not match the Python reference".into(),
                ));
            }
            println!("OK: Rust core matches the Python reference.");
            Ok(())
        }
        Some("step-response") => {
            for z in [0.5, 0.7, 1.0, 1.5] {
                println!("zeta={z:<4} overshoot={:.1}%", force::overshoot_pct(z));
            }
            Ok(())
        }
        _ => {
            println!("{USAGE}");
            Ok(())
        }
    }
}
