#![allow(dead_code)]
#[path="../../src/third_party/esa2026/src/dvec.rs"] pub mod dvec;
#[path="../../src/third_party/esa2026/src/query.rs"] pub mod query;
#[path="../../src/third_party/esa2026/src/kiddo.rs"] pub mod kiddo;
#[path="../../src/third_party/esa2026/src/nabo.rs"] pub mod nabo;
#[path="../../src/third_party/esa2026/src/neighbourhood.rs"] pub mod neighbourhood;
#[path="../../src/third_party/esa2026/src/vptree.rs"] pub mod vptree;
#[path="../../src/third_party/esa2026/src/orthtree.rs"] pub mod orthtree;
#[path="../../src/third_party/esa2026/src/grid.rs"] pub mod grid;
pub use query::Query;
pub type NodeId=usize;
pub mod graph { pub struct Graph; impl Graph {pub fn is_connected(&self,_a:usize,_b:usize)->bool{false}pub fn neighbors(&self,_i:usize)->&[usize]{&[]}pub fn weight(&self,_i:usize)->f64{1.0}} }
#[derive(Clone)] pub struct Embedding<'a,const D:usize>{pub positions:Vec<dvec::DVec<D>>,pub graph:&'a graph::Graph}
static GRAPH:graph::Graph=graph::Graph;
struct Spark<const D:usize>(sprk::Sprk<D,8,f64,u32>);
impl<const D:usize> Query<D> for Spark<D>{fn query_radius(&self,p:dvec::DVec<D>,r:f64,out:&mut Vec<usize>){self.0.query_radius(&p.components,r,out);}}
fn engine<const D:usize>(p:&[[u32;D]],kind:&str)->Box<dyn Query<D>> {
 let coords:Vec<[f64;D]>=p.iter().map(|p|p.map(|v|v as f64/4294967296.0)).collect();
 let e=Embedding{positions:coords.iter().map(|p|dvec::DVec::new(*p)).collect(),graph:&GRAPH};
 match kind{
 "esa_sprk"=>Box::new(Spark(sprk::Sprk::new(&coords))),
 "esa_kiddo"=>Box::new(kiddo::Kiddo::new(e)),
 "esa_nabo"=>Box::new(nabo::Nabo::new(e)),
 "esa_neighbourhood"=>Box::new(neighbourhood::Neihbourhood::new(e)),
 "esa_vptree"=>Box::new(vptree::VPTree::new(e)),
 "esa_orthtree"=>Box::new(orthtree::Orthtree::new(e)),
 "esa_grid"=>Box::new(grid::Grid::new(e)),
 _=>panic!("Unknown backend")}
}
fn query_point<const D:usize>(c:[u32;D])->dvec::DVec<D>{dvec::DVec::new(c.map(|x|x as f64/4294967296.0))}
include!("driver.rs");
