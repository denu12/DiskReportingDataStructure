// File-format and box-to-ball adapters; PGM iterator fixes are documented separately.
#pragma once
#include "disk_geometry_2d.h"

std::pair<Point,Point> query_box(const Data& d, std::size_t q) {
    std::uint64_t lo=0, hi=UINT64_MAX;
    while(lo<hi) { auto m=lo+(hi-lo)/2; if(Wide(m)*m<d.radii[q])lo=m+1;else hi=m; }
    Point lower(d.d),upper(d.d);
    for(unsigned a=0;a<d.d;++a) {
        auto c=d.centers[q][a];
        lower[a]=lo>c?0:c-lo;
        upper[a]=lo>UINT32_MAX-c?UINT32_MAX:c+lo;
    }
    return {lower,upper};
}
template<class P> bool inside_point(const Data& d,std::size_t q,const P& p) {
    Wide sum=0;
    for(unsigned a=0;a<d.d;++a) {
        auto delta=std::int64_t(p[a])-d.centers[q][a];
        auto v=std::uint64_t(delta<0?-delta:delta);sum+=Wide(v)*v;
    }
    return sum<=d.radii[q];
}
template<class Points> bool verify_points(const Data& d,std::size_t q,const Points& hits) {
    std::vector<Point> actual,expected;
    for(const auto& p:hits) { Point value(d.d);for(unsigned a=0;a<d.d;++a)value[a]=p[a];actual.push_back(value); }
    for(std::size_t i=0;i<d.points.size();++i)if(d.contains(i,q))expected.push_back(d.points[i]);
    std::sort(actual.begin(),actual.end());std::sort(expected.begin(),expected.end());
    return actual==expected;
}
const char* membership_contract="original_box_api_with_integer_ball_filter";

#if defined(ADDITIONAL_PGM)
#include "pgm/pgm_index_variants.hpp"
const char* output_contract="point_ids_only";
const char* output_representation="pgm_iterator_original_ids";

template<unsigned D> Query make_index(Data& d,const std::string&) {
    using Tree=pgm::MultidimensionalPGMIndex<D,std::uint64_t,64>;
    using P=typename Tree::value_type;
    using Morton=mortonnd::MortonNDBmi<D,std::uint64_t>;
    constexpr unsigned shift=32-(64/D-1);
    auto cell=[](const Point& p) {
        P v;[&]<std::size_t... A>(std::index_sequence<A...>){((std::get<A>(v)=std::uint64_t(p[A])>>shift),...);}(std::make_index_sequence<D>{});return v;
    };
    std::vector<P> cells;std::vector<std::pair<std::uint64_t,std::size_t>> records;
    for(std::size_t i=0;i<d.points.size();++i) {
        auto p=cell(d.points[i]);cells.push_back(p);
        records.emplace_back(std::apply([](auto... x){return Morton::Encode(x...);},p),i);
    }
    // Mirror native Morton-key order to attach IDs; equal keys may use any order.
    std::sort(records.begin(),records.end());
    struct Entry {std::size_t id; CoordinatePair point;};
    auto entries=std::make_shared<std::vector<Entry>>();
    entries->reserve(records.size());
    for(auto [key,id]:records)entries->push_back({id,{d.points[id][0],d.points[id][1]}});
    auto tree=std::make_shared<Tree>(cells.begin(),cells.end());
    auto hits=std::make_shared<std::vector<std::size_t>>();
    return {[&,tree,hits,entries](std::size_t q) {
        const Disk2D disk(d.centers[q], d.radii[q]);
        auto [lo,hi]=disk.bounds();
        hits->clear();
        for(auto it=tree->range(P{lo[0]>>shift,lo[1]>>shift},P{hi[0]>>shift,hi[1]>>shift});it!=tree->end();++it) {
            const auto& entry=(*entries)[it.source_position()];
            if(disk.contains(entry.point[0],entry.point[1]))hits->push_back(entry.id);
        }
    },[hits]{return hits->size();},[&,hits](std::size_t q){return verify_ids(d,q,*hits);}};
}
#elif defined(ADDITIONAL_SPATIALINDEX)
#include <spatialindex/SpatialIndex.h>
const char* output_contract="point_ids_only";
const char* output_representation="native_libspatialindex_ids";
struct SpatialStream:SpatialIndex::IDataStream {
    Data& data;std::size_t next=0;
    explicit SpatialStream(Data& d):data(d){}
    SpatialIndex::IData* getNext()override {
        if(!hasNext())return nullptr;
        std::vector<double> p(data.points[next].begin(),data.points[next].end());
        SpatialIndex::Region box(p.data(),p.data(),data.d);
        return new SpatialIndex::RTree::Data(0,nullptr,box,next++);
    }
    bool hasNext()override{return next<data.points.size();}
    std::uint32_t size()override{return data.points.size();}
    void rewind()override{next=0;}
};
struct SpatialDisk : SpatialIndex::Region {
    Disk2D disk;
    explicit SpatialDisk(Disk2D query) : disk(query) { makeDimension(2); }
    bool intersectsRegion(const SpatialIndex::Region& region) const override {
        const auto* lo = region.m_pLow;
        const auto* hi = region.m_pHigh;
        return disk.intersects({std::uint32_t(lo[0]), std::uint32_t(lo[1])},
                               {std::uint32_t(hi[0]), std::uint32_t(hi[1])});
    }
};
struct SpatialVisitor:SpatialIndex::IVisitor {
    std::vector<std::size_t> hits;
    void visitNode(const SpatialIndex::INode&)override{}
    void visitData(const SpatialIndex::IData& p)override {
        hits.push_back(p.getIdentifier());
    }
    void visitData(std::vector<const SpatialIndex::IData*>& values)override {for(auto p:values)visitData(*p);}
};
Query create(Data& d,const std::string& algorithm) {
    using namespace SpatialIndex;
    auto storage=std::shared_ptr<IStorageManager>(StorageManager::createNewMemoryStorageManager());
    auto variant=algorithm=="lsi_linear"?RTree::RV_LINEAR:algorithm=="lsi_quadratic"?RTree::RV_QUADRATIC:RTree::RV_RSTAR;
    id_type identifier;SpatialStream stream(d);
    auto tree=std::shared_ptr<ISpatialIndex>(algorithm=="lsi_str" && !d.points.empty()
        ? RTree::createAndBulkLoadNewRTree(RTree::BLM_STR,stream,*storage,.7,16,16,d.d,RTree::RV_RSTAR,identifier)
        : RTree::createNewRTree(*storage,variant==RTree::RV_RSTAR?.7:.5,16,16,d.d,variant,identifier));
    if(algorithm!="lsi_str")for(std::size_t i=0;i<d.points.size();++i) {
        std::vector<double> p(d.points[i].begin(),d.points[i].end());Region box(p.data(),p.data(),d.d);tree->insertData(0,nullptr,box,i);
    }
    auto visitor=std::make_shared<SpatialVisitor>();
    return {[&,storage,tree,visitor](std::size_t q) {
        visitor->hits.clear();
        const SpatialDisk disk(Disk2D(d.centers[q],d.radii[q]));
        tree->intersectsWithQuery(disk,*visitor);
    },[visitor]{return visitor->hits.size();},[&,visitor](std::size_t q){return verify_ids(d,q,visitor->hits);}};
}
#endif
#if defined(ADDITIONAL_PGM)
Query create(Data& d,const std::string& algorithm) {
    if(d.d==2)return make_index<2>(d,algorithm);
    throw std::runtime_error("Unsupported dimension for additional backend");
}
#endif
