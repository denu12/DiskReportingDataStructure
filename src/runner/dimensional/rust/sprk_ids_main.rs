#![allow(dead_code)]
#[path="../../../third_party/esa2026/src/dvec.rs"] pub mod dvec;
#[path="../../../third_party/esa2026/src/query.rs"] pub mod query;
#[path="../../../third_party/esa2026/src/kiddo.rs"] pub mod kiddo;
#[path="../../../third_party/esa2026/src/nabo.rs"] pub mod nabo;
#[path="../../../third_party/esa2026/src/neighbourhood.rs"] pub mod neighbourhood;
#[path="../../../third_party/esa2026/src/vptree.rs"] pub mod vptree;
#[path="../../../third_party/esa2026/src/orthtree.rs"] pub mod orthtree;
#[path="../../../third_party/esa2026/src/grid.rs"] pub mod grid;
pub use query::Query;
pub type NodeId=usize;
pub mod graph { pub struct Graph; impl Graph {pub fn is_connected(&self,_a:usize,_b:usize)->bool{false}pub fn neighbors(&self,_i:usize)->&[usize]{&[]}pub fn weight(&self,_i:usize)->f64{1.0}} }
#[derive(Clone)] pub struct Embedding<'a,const D:usize>{pub positions:Vec<dvec::DVec<D>>,pub graph:&'a graph::Graph}
static GRAPH:graph::Graph=graph::Graph;
struct Spark<const D:usize>(sprk::Sprk<D,8,f32,u32>);
impl<const D:usize> Query<D> for Spark<D>{fn query_radius(&self,p:dvec::DVec<D>,r:f64,out:&mut Vec<usize>){self.0.query_radius(&p.components.map(|x|x as f32),(r as f32).next_up(),out);}}
fn engine<const D:usize>(p:&[[u32;D]],kind:&str,radius_hint:f64)->Box<dyn Query<D>> {
 let coords:Vec<[f64;D]>=p.iter().map(|p|p.map(|v|v as f64/4294967296.0)).collect();
 let e=Embedding{positions:coords.iter().map(|p|dvec::DVec::new(*p)).collect(),graph:&GRAPH};
 match kind{
 "esa_sprk"=>Box::new(Spark(sprk::Sprk::new(&coords.iter().map(|p|p.map(|x|x as f32)).collect::<Vec<_>>()))),
 "esa_kiddo"=>Box::new(kiddo::Kiddo::new(e)),
 "esa_nabo"=>Box::new(nabo::Nabo::new(e)),
 "esa_neighbourhood"=>Box::new(neighbourhood::Neihbourhood::new(e)),
 "esa_vptree"=>Box::new(vptree::VPTree::new(e)),
 "esa_orthtree"=>Box::new(orthtree::Orthtree::new(e)),
 "esa_grid"=>Box::new(grid::Grid::new_with_radius(e,radius_hint)),
 _=>panic!("Unknown backend")}
}
fn query_point<const D:usize>(c:[u32;D])->dvec::DVec<D>{dvec::DVec::new(c.map(|x|x as f64/4294967296.0))}
const IDS_ONLY:bool=true;
fn search_radius<const D:usize>(r2:u128,kind:&str)->f64{
 let r=(r2 as f64).sqrt()/4294967296.0;
 if kind=="esa_sprk" {sprk::integer_reporting::candidate_radius::<D>(r) as f64}
 else {((r*r*(1.0+64.0*D as f64*f64::EPSILON)).next_up().sqrt()).next_up()}
}
include!("driver.rs");
