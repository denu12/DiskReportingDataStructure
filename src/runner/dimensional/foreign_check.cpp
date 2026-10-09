// Dimensional interfaces only; competitor source is not repaired.
#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <limits>
#include <numeric>
#include <vector>
#include <string>
#include <stdexcept>
#include <chrono>
using Wide=unsigned __int128;
using Point=std::vector<std::uint32_t>;
template<class T> T read(std::istream& f){T x{};if(!f.read((char*)&x,sizeof x))throw std::runtime_error("Truncated input");return x;}
struct Data {
 unsigned d; std::vector<Point> points,centers;std::vector<Wide> radii;
 explicit Data(const char* path){std::ifstream f(path,std::ios::binary);d=read<unsigned>(f);
 auto n=read<std::uint64_t>(f),q=read<std::uint64_t>(f);
 for(std::size_t i=0;i<n+q;++i){Point p(d);for(auto& x:p)x=read<std::uint32_t>(f);
 if(i<n)points.push_back(p);else{centers.push_back(p);Wide r=read<std::uint64_t>(f);r|=Wide(read<std::uint64_t>(f))<<64;radii.push_back(r);}}
 }
 bool contains(std::size_t id,std::size_t q)const{Wide sum=0;for(unsigned a=0;a<d;++a){auto diff=std::int64_t(points[id][a])-centers[q][a];auto v=std::uint64_t(diff<0?-diff:diff);sum+=Wide(v)*v;}return sum<=radii[q];}
 double radius(std::size_t q)const{
  double squared=double(radii[q])/18446744073709551616.;
  return std::nextafter(std::sqrt(std::nextafter(squared*(1+64*d*std::numeric_limits<double>::epsilon()),INFINITY)),INFINITY);
 }
 std::vector<double> center(std::size_t q)const{std::vector<double> v;for(auto x:centers[q])v.push_back(double(x)/4294967296.);return v;}
};
#if defined(BACKEND_NANO) || defined(BACKEND_BOOST)
// These local adapters write coordinates directly into the reusable final result.
using Query=std::function<void(std::size_t,std::vector<std::uint32_t>&)>;
#else
using Query=std::function<std::vector<std::size_t>(std::size_t)>;
#endif
#if defined(BACKEND_BRUTE)
Query create(Data& d,const std::string&){return [&](std::size_t q){std::vector<std::size_t> ids;for(std::size_t i=0;i<d.points.size();++i)if(d.contains(i,q))ids.push_back(i);return ids;};}
#elif defined(BACKEND_ANN)
#include <ANN/ANN.h>
Query create(Data& d,const std::string&){
 auto coords=std::make_shared<std::vector<std::vector<double>>>();for(auto& p:d.points){std::vector<double> v;for(auto x:p)v.push_back(double(x)/4294967296.);coords->push_back(v);}
 auto rows=std::make_shared<std::vector<ANNpoint>>();for(auto& p:*coords)rows->push_back(p.data());
 auto tree=std::make_shared<ANNkd_tree>(rows->data(),int(rows->size()),int(d.d));
 return [&,coords,rows,tree](std::size_t q){auto c=d.center(q);double r=d.radius(q);int n=tree->annkFRSearch(c.data(),r*r,0,nullptr,nullptr,0.0);std::vector<ANNidx> ids(n);if(n)tree->annkFRSearch(c.data(),r*r,n,ids.data(),nullptr,0.0);return std::vector<std::size_t>(ids.begin(),ids.end());};
}
#elif defined(BACKEND_NANO)
#include "nanoflann.hpp"
struct Cloud{unsigned dimension;std::vector<double> coordinates;
 explicit Cloud(const Data& d):dimension(d.d){coordinates.reserve(d.points.size()*d.d);for(const auto& p:d.points)for(auto x:p)coordinates.push_back(double(x)/4294967296.);}
 std::size_t kdtree_get_point_count()const{return coordinates.size()/dimension;}double kdtree_get_pt(std::size_t i,std::size_t a)const{return coordinates[i*dimension+a];}template<class B>bool kdtree_get_bbox(B&)const{return false;}};
Query create(Data& d,const std::string&){
 auto cloud=std::make_shared<Cloud>(d);
 using Tree=nanoflann::KDTreeSingleIndexAdaptor<nanoflann::L2_Simple_Adaptor<double,Cloud>,Cloud,-1,std::size_t>;
 // The constructor builds the index. Do not build it a second time.
 auto tree=std::make_shared<Tree>(d.d,*cloud,nanoflann::KDTreeSingleIndexAdaptorParams(10));
 return [&,cloud,tree,c=std::vector<double>(d.d),hits=std::vector<nanoflann::ResultItem<std::size_t,double>>{}]
 (std::size_t q,std::vector<std::uint32_t>& out) mutable {
  for(unsigned a=0;a<d.d;++a)c[a]=double(d.centers[q][a])/4294967296.;
  auto r=d.radius(q);hits.clear();
  tree->radiusSearch(c.data(),r*r,hits,nanoflann::SearchParameters(0,false));
  for(auto h:hits)if(d.contains(h.first,q)){const auto& p=d.points[h.first];out.insert(out.end(),p.begin(),p.end());}
 };
}
#elif defined(BACKEND_CGAL)
#include <CGAL/Cartesian_d.h>
#include <CGAL/Search_traits_d.h>
#include <CGAL/Kd_tree.h>
#include <CGAL/Fuzzy_sphere.h>
Query create(Data& d,const std::string&){
 using K=CGAL::Cartesian_d<double>;using P=K::Point_d;using Traits=CGAL::Search_traits_d<K>;using Tree=CGAL::Kd_tree<Traits>;
 std::vector<P> points;auto mapping=std::make_shared<std::map<std::vector<double>,std::vector<std::size_t>>>();
 for(std::size_t i=0;i<d.points.size();++i){std::vector<double> p;for(auto x:d.points[i])p.push_back(double(x)/4294967296.);points.emplace_back(d.d,p.begin(),p.end());(*mapping)[p].push_back(i);}
 auto tree=std::make_shared<Tree>(points.begin(),points.end());tree->build();
 return [&,tree,mapping](std::size_t q){auto c=d.center(q);std::vector<P> hits;tree->search(std::back_inserter(hits),CGAL::Fuzzy_sphere<Traits>(P(d.d,c.begin(),c.end()),d.radius(q),0.));std::map<std::vector<double>,std::size_t> used;std::vector<std::size_t> ids;for(auto& p:hits){std::vector<double> v(p.cartesian_begin(),p.cartesian_end());ids.push_back(mapping->at(v).at(used[v]++));}return ids;};
}
#elif defined(BACKEND_BOOST)
#include <boost/geometry.hpp>
#include <boost/geometry/index/rtree.hpp>
namespace bg=boost::geometry;namespace bi=bg::index;
template<unsigned D,class Policy> Query boost_index(Data& data){
 using P=bg::model::point<std::uint32_t,D,bg::cs::cartesian>;using Tree=bi::rtree<P,Policy>;
 auto point=[](const Point& p){P result;[&]<std::size_t... A>(std::index_sequence<A...>){(bg::set<A>(result,p[A]),...);}(std::make_index_sequence<D>{});return result;};
 std::vector<P> entries;entries.reserve(data.points.size());for(const auto& p:data.points)entries.push_back(point(p));
 auto tree=std::make_shared<Tree>(entries.begin(),entries.end());
 return [&,tree,point](std::size_t q,std::vector<std::uint32_t>& out){std::uint64_t low=0,high=UINT64_MAX;while(low<high){auto m=low+(high-low)/2;if(Wide(m)*m<data.radii[q])low=m+1;else high=m;}
 Point lo(D),hi(D);for(unsigned a=0;a<D;++a){auto c=data.centers[q][a];lo[a]=low>c?0:c-low;hi[a]=low>UINT32_MAX-c?UINT32_MAX:c+low;}
 auto inside=[&](const P& p){Wide sum=0;
  [&]<std::size_t... A>(std::index_sequence<A...>){
   auto add=[&](auto axis){auto delta=std::int64_t(bg::get<decltype(axis)::value>(p))-data.centers[q][axis];auto magnitude=std::uint64_t(delta<0?-delta:delta);sum+=Wide(magnitude)*magnitude;};
   (add(std::integral_constant<std::size_t,A>{}),...);
  }(std::make_index_sequence<D>{});return sum<=data.radii[q];};
 auto predicate=bi::intersects(bg::model::box<P>(point(lo),point(hi))) && bi::satisfies(inside);
 for(auto it=tree->qbegin(predicate);it!=tree->qend();++it)
  [&]<std::size_t... A>(std::index_sequence<A...>){(out.push_back(bg::get<A>(*it)),...);}(std::make_index_sequence<D>{});
 };
}
template<unsigned D>Query select_boost(Data& d,const std::string& a){if(a=="boost_lin")return boost_index<D,bi::linear<16>>(d);if(a=="boost_quad")return boost_index<D,bi::quadratic<16>>(d);return boost_index<D,bi::rstar<16>>(d);}
Query create(Data& d,const std::string& a){switch(d.d){
#define DIM(N) case N:return select_boost<N>(d,a);
DIM(2) DIM(3) DIM(4) DIM(5) DIM(6) DIM(7) DIM(8) DIM(9) DIM(10) DIM(11) DIM(12) DIM(13) DIM(14) DIM(15) DIM(16) DIM(32)
#undef DIM
default:throw std::runtime_error("Unsupported dimension");}}
#endif
int main(int argc,char** argv){try{if(argc!=3 && argc!=4)throw std::runtime_error("Usage: foreign_check CASE ALGORITHM [--bench]");bool bench=argc==4 && std::string(argv[3])=="--bench";Data data(argv[1]);Query query;auto start=std::chrono::steady_clock::now();if(!data.points.empty())query=create(data,argv[2]);double build_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();double query_seconds=0;std::size_t answers=0;
std::vector<std::uint32_t> reported;auto batch_start=std::chrono::steady_clock::now();for(std::size_t q=0;q<data.centers.size();++q){if(!bench)start=std::chrono::steady_clock::now();reported.clear();
#if defined(BACKEND_NANO) || defined(BACKEND_BOOST)
if(query)query(q,reported);
#else
auto ids=query?query(q):std::vector<std::size_t>{};reported.reserve(ids.size()*data.d);for(auto id:ids)if(data.contains(id,q)){const auto& p=data.points.at(id);reported.insert(reported.end(),p.begin(),p.end());}
#endif
if(!bench)query_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();answers+=reported.size()/data.d;if(bench)continue;std::vector<Point> actual;for(std::size_t i=0;i<reported.size();i+=data.d)actual.emplace_back(reported.begin()+i,reported.begin()+i+data.d);std::vector<Point> expected;for(std::size_t i=0;i<data.points.size();++i)if(data.contains(i,q))expected.push_back(data.points[i]);std::sort(expected.begin(),expected.end());std::sort(actual.begin(),actual.end());if(actual!=expected){std::cout<<"{\"status\":\"incorrect\",\"query\":"<<q<<",\"actual_count\":"<<actual.size()<<",\"expected_count\":"<<expected.size()<<"}\n";return 2;}}
if(bench)query_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-batch_start).count();
std::cout<<"{\"status\":\"success\",\"queries\":"<<data.centers.size()<<",\"answers\":"<<answers<<",\"build_seconds\":"<<build_seconds<<",\"query_seconds\":"<<query_seconds<<"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
