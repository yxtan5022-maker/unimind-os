use std::f64::consts::FRAC_PI_2;

#[derive(Clone, Copy)]
pub struct UnibitConfig {
    pub phase_shift: f64,
    pub collapse_threshold: f64,
    pub entropy_window: usize,
    pub weight_floor: f64,
}

impl Default for UnibitConfig {
    fn default() -> Self {
        Self {
            phase_shift: 0.42,
            collapse_threshold: 0.707,
            entropy_window: 5,
            weight_floor: 0.85,
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

    pub fn fold_bits(&self, bits: &[u8]) -> Vec<f64> {
        bits.iter()
            .enumerate()
            .map(|(i, &b)| {
                let bit = if b == 0 { 0.0 } else { 1.0 };
                let weight = self.dynamic_weight(bits, i);
                (bit * FRAC_PI_2 + self.cfg.phase_shift).sin() * weight
            })
            .collect()
    }

    pub fn collapse_signal(&self, folded: &[f64]) -> Vec<u8> {
        folded
            .iter()
            .map(|&s| if s.abs() > self.cfg.collapse_threshold { 1 } else { 0 })
            .collect()
    }

    pub fn virtual_expand_signal(&self, folded: &[f64], factor: usize) -> Vec<f64> {
        let factor = factor.max(1);
        let mut out = Vec::with_capacity(folded.len() * factor);
        for (i, &v) in folded.iter().enumerate() {
            for j in 0..factor {
                let phase = (j as f64) * 0.03;
                out.push(v * (phase.cos()) + (i as f64 * 0.0001).sin() * 0.0005);
            }
        }
        out
    }

    fn dynamic_weight(&self, bits: &[u8], idx: usize) -> f64 {
        let window = self.cfg.entropy_window.max(1);
        let start = idx.saturating_sub(window / 2);
        let end = (idx + (window / 2) + 1).min(bits.len());

        let mut ones = 0usize;
        let mut total = 0usize;
        for &b in &bits[start..end] {
            total += 1;
            if b != 0 {
                ones += 1;
            }
        }

        let p1 = if total == 0 { 0.0 } else { ones as f64 / total as f64 };
        let p0 = 1.0 - p1;
        let entropy = shannon_entropy_2(p0, p1);

        let normalized_entropy = (entropy / 1.0).clamp(0.0, 1.0);
        let w = self.cfg.weight_floor + (1.0 - self.cfg.weight_floor) * (1.0 - normalized_entropy);
        w.clamp(self.cfg.weight_floor, 1.0)
    }
}

fn shannon_entropy_2(p0: f64, p1: f64) -> f64 {
    let mut h = 0.0;
    if p0 > 0.0 {
        h -= p0 * p0.log2();
    }
    if p1 > 0.0 {
        h -= p1 * p1.log2();
    }
    h
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fold_then_collapse_roundtrip() {
        let engine = UnibitEngine::default();
        let bits = [1u8, 0, 1, 1, 0, 1, 0, 0, 1, 1];
        let folded = engine.fold_bits(&bits);
        let recovered = engine.collapse_signal(&folded);
        assert_eq!(recovered, bits);
    }

    #[test]
    fn virtual_expansion_preserves_length_multiple() {
        let engine = UnibitEngine::default();
        let folded = vec![0.1, 0.2, 0.3];
        let expanded = engine.virtual_expand_signal(&folded, 4);
        assert_eq!(expanded.len(), 12);
    }
}

