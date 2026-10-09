//! Local exact-integer reporting adapter around the upstream f32 SIMD query.
//! Candidate IDs use the native writer. Gathering, exact membership and writing
//! the requested output are all performed by the timed caller.
use crate::tree::Sprk;

/// Conservative envelope for uint32 coordinates normalized by 2^32.
/// The absolute term covers f32 coordinate rounding; the relative term covers
/// distance arithmetic. Higher-dimensional half-distance kernels also need a
/// cancellation allowance because they subtract dot products of absolute positions.
pub fn candidate_radius<const D: usize>(radius: f64) -> f32 {
    let epsilon = f32::EPSILON as f64;
    let rounded = radius + 2.0 * (D as f64).sqrt() * epsilon;
    let squared = rounded * rounded * (1.0 + 64.0 * D as f64 * epsilon)
        + if D >= 6 { 32.0 * (D * D) as f64 * epsilon } else { 0.0 };
    (squared.sqrt() as f32).next_up()
}

pub struct IntegerPointSprk {
    tree: Option<Sprk<2, 8, f32, u32>>,
    points: Vec<[u32; 2]>,
    candidates: Vec<usize>,
}
impl IntegerPointSprk {
    pub fn new(points: &[[u32; 2]]) -> Self {
        let coords: Vec<_> = points.iter().map(|p| p.map(|x| (x as f64 / 4294967296.0) as f32)).collect();
        Self { tree: if points.is_empty() { None } else { Some(Sprk::new(&coords)) },
               points: points.to_vec(), candidates: Vec::new() }
    }
    fn candidates(&mut self, center: [u32; 2], radius2: u128) {
        self.candidates.clear();
        if let Some(tree) = &self.tree {
            let pos = center.map(|x| (x as f64 / 4294967296.0) as f32);
            let radius = candidate_radius::<2>((radius2 as f64).sqrt() / 4294967296.0);
            tree.query_radius(&pos, radius, &mut self.candidates);
        }
    }
    fn contains(point: [u32; 2], center: [u32; 2], radius2: u128) -> bool {
        let dx = (point[0] as i64 - center[0] as i64).unsigned_abs() as u128;
        let dy = (point[1] as i64 - center[1] as i64).unsigned_abs() as u128;
        dx * dx + dy * dy <= radius2
    }
    pub fn query_points(&mut self, center: [u32; 2], radius2: u128, out: &mut Vec<[u32; 2]>) {
        self.candidates(center, radius2);
        for &id in &self.candidates {
            let point = self.points[id];
            if Self::contains(point, center, radius2) { out.push(point); }
        }
    }
    pub fn query_ids(&mut self, center: [u32; 2], radius2: u128, out: &mut Vec<usize>) {
        self.candidates(center, radius2);
        for &id in &self.candidates {
            if Self::contains(self.points[id], center, radius2) { out.push(id); }
        }
    }
}
