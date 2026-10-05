//! Small deterministic PRNG (xoshiro256** seeded through SplitMix64) so the crate stays dependency-free.
//! NOTE: not bit-compatible with NumPy's PCG64; cross-language parity is checked on exported *vectors*
//! (see `reference`), not on the random stream.
pub struct Rng {
    s: [u64; 4],
}
fn splitmix(x: &mut u64) -> u64 {
    *x = x.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut z = *x;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}
impl Rng {
    pub fn new(seed: u64) -> Self {
        let mut x = seed;
        Rng {
            s: [
                splitmix(&mut x),
                splitmix(&mut x),
                splitmix(&mut x),
                splitmix(&mut x),
            ],
        }
    }
    pub fn next_u64(&mut self) -> u64 {
        let r = self.s[1].wrapping_mul(5).rotate_left(7).wrapping_mul(9);
        let t = self.s[1] << 17;
        self.s[2] ^= self.s[0];
        self.s[3] ^= self.s[1];
        self.s[1] ^= self.s[2];
        self.s[0] ^= self.s[3];
        self.s[2] ^= t;
        self.s[3] = self.s[3].rotate_left(45);
        r
    }
    /// Uniform in [0, 1) with 53 random bits.
    pub fn next_f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
    }
    /// Uniform integer in [0, n) (rejection-free modulo bias is < 2^-60 for n ≤ 16).
    pub fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }
    /// `m` distinct indices from 0..n (partial Fisher–Yates).
    pub fn sample_distinct<const M: usize>(&mut self, n: usize) -> [usize; M] {
        let mut pool: Vec<usize> = (0..n).collect();
        let mut out = [0; M];
        for i in 0..M {
            let j = i + self.below(n - i);
            pool.swap(i, j);
            out[i] = pool[i];
        }
        out
    }
}
