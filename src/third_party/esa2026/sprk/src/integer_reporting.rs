//! Manual adaptation of SPRK reporting for original uint32 point output.
//! Upstream construction, traversal and floating-point candidate distances are
//! retained. Integer payloads follow the exact SIMD block/lane order, including
//! leaf padding. No input-order ID lookup is performed during reporting.
use crate::tree::{LeafRange, Sprk};

/// Static two-dimensional SPRK with leaf-local integer point payloads.
pub struct IntegerPointSprk {
    tree: Sprk<2, 8, f64, u32>,
    points: Vec<[[u32; 2]; 8]>,
    valid: Vec<[bool; 8]>,
    ranges: Vec<LeafRange>,
}

impl IntegerPointSprk {
    /// Build the tree and its integer payloads; both are construction costs.
    pub fn new(points: &[[u32; 2]]) -> Self {
        let coords: Vec<_> = points.iter().map(|p| p.map(|x| x as f64 / 4294967296.0)).collect();
        let tree = Sprk::<2, 8, f64, u32>::new(&coords);
        let valid = tree.positions_sorted.iter().map(|b| b.ids.map(|id| (id as usize) < points.len())).collect();
        let payload = tree.positions_sorted.iter().map(|b| b.ids.map(|id| points.get(id as usize).copied().unwrap_or([0, 0]))).collect();
        Self { tree, points: payload, valid, ranges: Vec::new() }
    }

    /// Append each exact matching integer point explicitly, preserving multiplicity.
    pub fn query_points(&mut self, center: [u32; 2], radius2: u128, out: &mut Vec<[u32; 2]>) {
        if self.points.is_empty() { return; }
        let pos = center.map(|x| x as f64 / 4294967296.0);
        // Same conservative floating-point envelope as the existing adapter.
        let radius = (radius2 as f64 / 18446744073709551616.0 + 64.0 * f64::EPSILON).sqrt();
        let threshold = radius * radius;
        self.ranges.clear();
        self.tree.collect_ranges(&pos, 0, 0, threshold, &mut [0.0; 2], &mut self.ranges);
        for range in &self.ranges {
            for block in range.min_i..range.max_i {
                let distances = self.tree.positions_sorted[block].dist_squared(pos);
                for lane in 0..8 {
                    if self.valid[block][lane] && distances[lane] <= threshold {
                        let p = self.points[block][lane];
                        let dx = p[0] as i128 - center[0] as i128;
                        let dy = p[1] as i128 - center[1] as i128;
                        if (dx * dx + dy * dy) as u128 <= radius2 { out.push(p); }
                    }
                }
            }
        }
    }
}
