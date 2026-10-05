//! Percentile helpers (NumPy-style linear interpolation) and latency summaries.
pub fn percentile(sorted: &[f64], q: f64) -> f64 {
    if sorted.is_empty() {
        return f64::NAN;
    }
    let pos = q / 100.0 * (sorted.len() - 1) as f64;
    let (lo, hi) = (pos.floor() as usize, pos.ceil() as usize);
    sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo as f64)
}
#[derive(Debug, Clone, Copy)]
pub struct Latency {
    pub n: usize,
    pub median_us: f64,
    pub p95_us: f64,
    pub p999_us: f64,
    pub max_us: f64,
    pub mean_us: f64,
}
/// `ns`: per-call latencies in nanoseconds.
pub fn latency_summary(ns: &mut [u128]) -> Latency {
    ns.sort_unstable();
    let v: Vec<f64> = ns.iter().map(|&x| x as f64 / 1e3).collect();
    Latency {
        n: v.len(),
        median_us: percentile(&v, 50.0),
        p95_us: percentile(&v, 95.0),
        p999_us: percentile(&v, 99.9),
        max_us: *v.last().unwrap_or(&f64::NAN),
        mean_us: v.iter().sum::<f64>() / v.len().max(1) as f64,
    }
}
