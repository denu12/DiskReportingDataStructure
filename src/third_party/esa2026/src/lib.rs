#![allow(dead_code)]
pub mod dvec; pub mod query; pub mod kiddo; pub mod nabo; pub mod neighbourhood; pub mod vptree; pub mod orthtree; pub mod grid;
pub use query::Query;
pub type NodeId=usize;
pub mod graph { pub struct Graph; impl Graph { pub fn is_connected(&self,_a:usize,_b:usize)->bool{false} pub fn neighbors(&self,_i:usize)->&[usize]{&[]} pub fn weight(&self,_i:usize)->f64{1.0} } }
#[derive(Clone)] pub struct Embedding<'a,const D:usize>{pub positions:Vec<dvec::DVec<D>>, pub graph:&'a graph::Graph}
static GRAPH:graph::Graph=graph::Graph;
use pyo3::prelude::*;
use dvec::DVec;
struct Spark(sprk::Sprk<2,8,f64,u32>);
impl Query<2> for Spark { fn query_radius(&self,p:DVec<2>,r:f64,out:&mut Vec<usize>){ let mut ids:Vec<u32>=Vec::new(); self.0.query_radius(&p.components,r,&mut ids); out.extend(ids.into_iter().map(|i|i as usize)); } }
struct PyIndex { tree:Py<PyAny>, snn:bool }
impl PyIndex {
 fn new(points:&[[f64;2]],kind:u32)->Self { Python::attach(|py| {
  let np=py.import("numpy").unwrap();
  let data=np.call_method1("array",(points.to_vec(),)).unwrap();
  let snn=kind==9;
  let tree=if snn { py.import("snnpy").unwrap().getattr("build_snn_model").unwrap().call1((data,0)).unwrap() }
   else {py.import("sklearn.neighbors").unwrap().getattr(if kind==7 {"KDTree"}else{"BallTree"}).unwrap().call1((data,)).unwrap()};
  Self{tree:tree.unbind(),snn}
 }) }
}
impl Query<2> for PyIndex { fn query_radius(&self,p:DVec<2>,r:f64,out:&mut Vec<usize>){Python::attach(|py|{
 let np=py.import("numpy").unwrap();
 let arr=np.call_method1("array",(p.components.to_vec(),)).unwrap();
 let arr=if self.snn {arr}else{arr.call_method1("reshape",((1,2),)).unwrap()};
 let result=self.tree.bind(py).call_method1("query_radius",(arr,r)).unwrap();
 let result=if self.snn{result}else{result.get_item(0).unwrap()};
 out.extend(result.call_method0("tolist").unwrap().extract::<Vec<usize>>().unwrap());
 });} }
struct Index { points:Vec<[u32;2]>, engine:Option<Box<dyn Query<2>>>, hits:Vec<usize>, output:Vec<[u32;2]> }
#[unsafe(no_mangle)] pub unsafe extern "C" fn esa_create(kind:u32,p:*const u32,n:usize)->*mut std::ffi::c_void {
 let points=unsafe{std::slice::from_raw_parts(p.cast::<[u32;2]>(),n)}.to_vec();
 let coords:Vec<[f64;2]>=points.iter().map(|p|p.map(|x|x as f64/4294967296.0)).collect();
 let e=Embedding{positions:coords.iter().map(|p|DVec::new(*p)).collect(),graph:&GRAPH};
 let engine:Option<Box<dyn Query<2>>>=if n==0{None}else{Some(match kind {
 0=>Box::new(Spark(sprk::Sprk::new(&coords))),
 1=>Box::new(kiddo::Kiddo::new(e)),
 2=>Box::new(nabo::Nabo::new(e)),
 3=>Box::new(neighbourhood::Neihbourhood::new(e)),
 4=>Box::new(vptree::VPTree::new(e)),
 5=>Box::new(orthtree::Orthtree::new(e)),
 6=>Box::new(grid::Grid::new(e)),
 7|8|9=>Box::new(PyIndex::new(&coords,kind)),
 _=>panic!("unknown ESA backend"),
 })};
 Box::into_raw(Box::new(Index{points,engine,hits:Vec::new(),output:Vec::new()})).cast()
}
#[unsafe(no_mangle)] pub unsafe extern "C" fn esa_destroy(p:*mut std::ffi::c_void){drop(unsafe{Box::from_raw(p.cast::<Index>())});}
#[unsafe(no_mangle)] pub unsafe extern "C" fn esa_query(p:*mut std::ffi::c_void,x0:u32,y0:u32,x1:u32,y1:u32,out:*mut *const u32)->usize{
 let index=unsafe{&mut *p.cast::<Index>()}; index.hits.clear();index.output.clear();
 if x0<=x1 && y0<=y1 {if let Some(engine)=&index.engine {
 let center=DVec::new([(x0 as f64+x1 as f64)/8589934592.0,(y0 as f64+y1 as f64)/8589934592.0]);
 let dx=(x1 as f64-x0 as f64)/8589934592.0; let dy=(y1 as f64-y0 as f64)/8589934592.0;
 // Conservative absolute margin covers SNN's cancellation in squared distances.
 let r=(dx*dx+dy*dy+64.0*f64::EPSILON).sqrt();
 engine.query_radius(center,r,&mut index.hits);
 for &id in &index.hits {let q=index.points[id];if q[0]>=x0&&q[0]<=x1&&q[1]>=y0&&q[1]<=y1{index.output.push(q);}}
 }}
 unsafe{*out=index.output.as_ptr().cast()};index.output.len()
}


mod dynamic_kiddo;

// Circle campaign ABI: unchanged upstream engines, original integer output.
#[unsafe(no_mangle)] pub unsafe extern "C" fn esa_circle_query(p:*mut std::ffi::c_void,x:u32,y:u32,r:f64,out:*mut *const u32)->usize {
 let index=unsafe{&mut *p.cast::<Index>()};index.hits.clear();index.output.clear();
 if let Some(engine)=&index.engine {
  engine.query_radius(DVec::new([x as f64/4294967296.0,y as f64/4294967296.0]),r,&mut index.hits);
  for &id in &index.hits { index.output.push(index.points[id]); }
 }
 unsafe{*out=index.output.as_ptr().cast()};index.output.len()
}
