use std::io::Read;
fn u32_read(f:&mut impl Read)->u32{let mut b=[0;4];f.read_exact(&mut b).unwrap();u32::from_le_bytes(b)}
fn u64_read(f:&mut impl Read)->u64{let mut b=[0;8];f.read_exact(&mut b).unwrap();u64::from_le_bytes(b)}
fn run<const D:usize>(f:&mut impl Read,kind:&str){
 assert_eq!(kind,"esa_sprk_CHEATING_IDS_ONLY");
 let n=u64_read(f) as usize;let q=u64_read(f) as usize;
 let points:Vec<[u32;D]>=(0..n).map(|_|std::array::from_fn(|_|u32_read(f))).collect();
 let bench=std::env::args().any(|x|x=="--bench");
 let start=std::time::Instant::now();let tree=if n==0{None}else{Some(engine(&points,"esa_sprk"))};let build_seconds=start.elapsed().as_secs_f64();let mut query_seconds=0.0;let mut answers=0;
 let mut ids=Vec::new();let mut actual=Vec::new();
 for j in 0..q{let center:[u32;D]=std::array::from_fn(|_|u32_read(f));let low=u64_read(f) as u128;let r2=low|((u64_read(f) as u128)<<64);
 ids.clear();actual.clear();let start=std::time::Instant::now();if let Some(t)=&tree{t.query_radius(query_point(center),(r2 as f64).sqrt()/4294967296.0,&mut ids);}std::hint::black_box(&ids);query_seconds+=start.elapsed().as_secs_f64();answers+=ids.len();if bench{continue;}
 // Resolve coordinates for the exact oracle only after stopping the query timer.
 actual.extend(ids.iter().map(|&i|points[i]));
 let mut expected:Vec<[u32;D]>=points.iter().enumerate().filter_map(|(i,p)|{let dist:u128=p.iter().zip(center).map(|(x,y)|{let v=(*x as i64-y as i64).unsigned_abs() as u128;v*v}).sum();if dist<=r2{Some(*p)}else{None}}).collect();
 expected.sort_unstable();actual.sort_unstable();if actual!=expected{println!("{{\"status\":\"incorrect\",\"query\":{},\"actual_count\":{},\"expected_count\":{}}}",j,actual.len(),expected.len());std::process::exit(2);}}
 println!("{{\"status\":\"success\",\"queries\":{},\"answers\":{},\"build_seconds\":{},\"query_seconds\":{},\"output_contract\":\"point_ids_only\"}}",q,answers,build_seconds,query_seconds);
}
fn main(){let args:Vec<String>=std::env::args().collect();let mut f=std::fs::File::open(&args[1]).unwrap();let d=u32_read(&mut f);
 match d{3=>run::<3>(&mut f,&args[2]),_=>panic!("SPRK IDs-only entry supports the 3D theater")}
}
