use std::io::Read;
fn u32_read(f:&mut impl Read)->u32{let mut b=[0;4];f.read_exact(&mut b).unwrap();u32::from_le_bytes(b)}
fn u64_read(f:&mut impl Read)->u64{let mut b=[0;8];f.read_exact(&mut b).unwrap();u64::from_le_bytes(b)}
fn run<const D:usize>(f:&mut impl Read,kind:&str){
 let n=u64_read(f) as usize;let q=u64_read(f) as usize;
 let points:Vec<[u32;D]>=(0..n).map(|_|std::array::from_fn(|_|u32_read(f))).collect();
 let bench=std::env::args().any(|x|x=="--bench");
 let start=std::time::Instant::now();let tree=if n==0{None}else{Some(engine(&points,kind))};let build_seconds=start.elapsed().as_secs_f64();let mut query_seconds=0.0;let mut answers=0;
 let mut ids=Vec::new();let mut actual=Vec::new();
 for j in 0..q{let center:[u32;D]=std::array::from_fn(|_|u32_read(f));let low=u64_read(f) as u128;let r2=low|((u64_read(f) as u128)<<64);
 ids.clear();actual.clear();let start=std::time::Instant::now();if let Some(t)=&tree{t.query_radius(query_point(center),(r2 as f64).sqrt()/4294967296.0,&mut ids);}actual.extend(ids.iter().map(|&i|points[i]));std::hint::black_box(&actual);query_seconds+=start.elapsed().as_secs_f64();answers+=actual.len();if bench{continue;}
 let mut expected:Vec<[u32;D]>=points.iter().enumerate().filter_map(|(i,p)|{let dist:u128=p.iter().zip(center).map(|(x,y)|{let v=(*x as i64-y as i64).unsigned_abs() as u128;v*v}).sum();if dist<=r2{Some(*p)}else{None}}).collect();
 expected.sort_unstable();actual.sort_unstable();if actual!=expected{println!("{{\"status\":\"incorrect\",\"query\":{},\"actual_count\":{},\"expected_count\":{}}}",j,actual.len(),expected.len());std::process::exit(2);}}
 println!("{{\"status\":\"success\",\"queries\":{},\"answers\":{},\"build_seconds\":{},\"query_seconds\":{}}}",q,answers,build_seconds,query_seconds);
}
fn main(){let args:Vec<String>=std::env::args().collect();let mut f=std::fs::File::open(&args[1]).unwrap();let d=u32_read(&mut f);
 match d{2=>run::<2>(&mut f,&args[2]),3=>run::<3>(&mut f,&args[2]),4=>run::<4>(&mut f,&args[2]),5=>run::<5>(&mut f,&args[2]),6=>run::<6>(&mut f,&args[2]),7=>run::<7>(&mut f,&args[2]),8=>run::<8>(&mut f,&args[2]),9=>run::<9>(&mut f,&args[2]),10=>run::<10>(&mut f,&args[2]),11=>run::<11>(&mut f,&args[2]),12=>run::<12>(&mut f,&args[2]),13=>run::<13>(&mut f,&args[2]),14=>run::<14>(&mut f,&args[2]),15=>run::<15>(&mut f,&args[2]),16=>run::<16>(&mut f,&args[2]),32=>run::<32>(&mut f,&args[2]),_=>panic!("Unsupported dimension")}
}
