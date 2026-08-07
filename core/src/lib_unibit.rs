use std::f64::consts::PI;

#[derive(Clone, Copy)]
pub struct UnibitConfig {
    pub phase_shift: f64,
    pub collapse_threshold: f64,
    pub window_delta: usize,
}

impl Default for UnibitConfig {
    fn default() -> Self {
        Self {
            phase_shift: 0.42,
            collapse_threshold: 0.707,
            window_delta: 2,
        }
    }
}

pub struct UnibitEngine {
    cfg: UnibitConfig,
}

impl Default for UnibitEngine {
    fn default() -> Self {
        Self::new(UnibitConfig::default())
    }
}

impl UnibitEngine {
    pub fn new(cfg: UnibitConfig) -> Self {
        Self { cfg }
    }

    /// Paper Eqs. 2-3: sliding-window frequency estimation followed by sinc
    /// folding. s_i = w_i * sinc((i + phi) * pi / n).
    pub fn fold_bits(&self, bits: &[u8]) -> Vec<f64> {
        let n = bits.len();
        let mut out = Vec::with_capacity(n);
        for i in 0..n {
            let start = i.saturating_sub(self.cfg.window_delta);
            let end = (i + self.cfg.window_delta + 1).min(n);
            let mut ones = 0usize;
            for &b in &bits[start..end] {
                if b != 0 {
                    ones += 1;
                }
            }
            let w = ones as f64 / (end - start) as f64;
            let x = ((i as f64) + self.cfg.phase_shift) * PI / n as f64;
            let sinc = if x.abs() < 1e-12 { 1.0 } else { x.sin() / x };
            out.push(w * sinc);
        }
        out
    }

    pub fn collapse_signal(&self, folded: &[f64]) -> Vec<u8> {
        folded
            .iter()
            .map(|&s| if s.abs() > self.cfg.collapse_threshold { 1 } else { 0 })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fold_length_preserved() {
        let engine = UnibitEngine::default();
        let bits = [1u8, 0, 1, 1, 0, 1, 0, 0, 1, 1];
        assert_eq!(engine.fold_bits(&bits).len(), bits.len());
    }

    #[test]
    fn fold_all_zeros_is_zero() {
        let engine = UnibitEngine::default();
        let bits = [0u8, 0, 0, 0, 0];
        assert!(engine.fold_bits(&bits).iter().all(|&s| s == 0.0));
    }

    #[test]
    fn fold_all_ones_equals_sinc_envelope() {
        let engine = UnibitEngine::default();
        let n = 5usize;
        let bits = [1u8; 5];
        let folded = engine.fold_bits(&bits);
        for (i, &s) in folded.iter().enumerate() {
            let x = (i as f64 + 0.42) * PI / n as f64;
            let expected = x.sin() / x;
            assert!((s - expected).abs() < 1e-12);
        }
    }

    #[test]
    fn collapse_threshold_behavior() {
        let engine = UnibitEngine::default();
        let folded = vec![0.9, 0.1, -0.8, -0.05];
        assert_eq!(engine.collapse_signal(&folded), vec![1, 0, 1, 0]);
    }
}
