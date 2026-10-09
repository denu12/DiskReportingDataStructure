#include "app/algorithms/static/esa2026.hh"
#include "app/algorithms/static/adapter.hh"
namespace diskreport::sfc::app::algorithms::sfc {
// SPRK (adapted): the Rust vector is the final, explicitly enumerated point
// result. Its writes and growth are timed; no second C++ result is required.
namespace {
esa_campaign::Result run_sprk_points(const esa_campaign::Dataset& data,bool verify) {
 if(!data.events.empty())throw std::runtime_error("SPRK (adapted) is static only");
 auto started=std::chrono::steady_clock::now();
 auto& api=EsaApi::get();
 if(!api.integer_search)throw std::runtime_error("Integer SPRK bridge unavailable");
 std::vector<uint32_t> points;points.reserve(2*data.points.size());
 for(auto p:data.points){points.push_back(p.x);points.push_back(p.y);}
 static const uint32_t empty[2]={};
 void* index=api.create(10,points.empty()?empty:points.data(),data.points.size());
 struct Owner{void* index;EsaApi& api;~Owner(){api.destroy(index);}} owner{index,api};
 esa_campaign::Result result;result.build_seconds=esa_campaign::elapsed(started);
 for(size_t i=0;i<data.queries.size();++i){
  const auto& c=data.queries[i];const uint32_t* output=nullptr;
  started=std::chrono::steady_clock::now();
  const size_t count=api.integer_search(index,c.x,c.y,c.radius2_lo,c.radius2_hi,&output);
  result.answers+=count;++result.queries;result.query_seconds+=esa_campaign::elapsed(started);
  if(verify){
   std::vector<uint64_t> actual;actual.reserve(count);
   for(size_t j=0;j<count;++j)actual.push_back(esa_campaign::key(output[2*j],output[2*j+1]));
   std::sort(actual.begin(),actual.end());
   if(actual!=esa_campaign::truth(data,c)){result.correct=false;result.failed_query=i;return result;}
  }
 }
 return result;
}
const bool integer_sprk_registered=[] {
 esa_campaign::registry()["esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS"]=run_sprk_points;
 return true;
}();
}

using Esa1Algo=Algo<Esa2026<1>>; REGISTER_IMPL_NAMED(Esa1Algo,"esa_kiddo");
using Esa2Algo=Algo<Esa2026<2>>; REGISTER_IMPL_NAMED(Esa2Algo,"esa_nabo");
using Esa3Algo=Algo<Esa2026<3>>; REGISTER_IMPL_NAMED(Esa3Algo,"esa_neighbourhood");
using Esa4Algo=Algo<Esa2026<4>>; REGISTER_IMPL_NAMED(Esa4Algo,"esa_vptree");
using Esa5Algo=Algo<Esa2026<5>>; REGISTER_IMPL_NAMED(Esa5Algo,"esa_orthtree");
using Esa6Algo=Algo<Esa2026<6>>; REGISTER_IMPL_NAMED(Esa6Algo,"esa_grid");
using Esa7Algo=Algo<Esa2026<7>>; REGISTER_IMPL_NAMED(Esa7Algo,"esa_sklearn_kd");
using Esa8Algo=Algo<Esa2026<8>>; REGISTER_IMPL_NAMED(Esa8Algo,"esa_sklearn_ball");
using Esa9Algo=Algo<Esa2026<9>>; REGISTER_IMPL_NAMED(Esa9Algo,"esa_snn");
using EsaNanoAlgo=Algo<EsaNanoflann>; REGISTER_IMPL_NAMED(EsaNanoAlgo,"esa_nanoflann");
}
