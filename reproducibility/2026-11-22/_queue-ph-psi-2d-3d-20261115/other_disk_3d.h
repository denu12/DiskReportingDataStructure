#pragma once

#if defined(FOLLOWUP_INDEXICON)
#include "kdtree.hpp"

template<bool WideRadius> struct IndexiconSphere {
    Ball<3,WideRadius> ball;
    unsigned classifyNode(const auto& low, const auto& high) const {
        Box<3> box;
        for (unsigned a=0;a<3;++a) {
            box.low[a]=std::clamp(low[a],0.,double(UINT32_MAX));
            box.high[a]=std::ceil(std::clamp(high[a],0.,double(UINT32_MAX)));
        }
        return static_cast<unsigned>(ball.classify(box));
    }
    bool containsPoint(const auto& p) const { return ball.contains(p); }
};

template<KDSplit Strategy>
int indexicon_run(const Case<3>& data, bool verify) {
    const auto start=Clock::now();
    using Key=KDPoint<double,3>;
    using Tree=KDTree<double,Id,3,128,Strategy>;
    std::vector<std::pair<Key,Id>> entries;
    entries.reserve(data.points.size());
    for (Id id=0;id<data.points.size();++id) {
        const auto& p=data.points[id];
        entries.emplace_back(Key(p[0],p[1],p[2]),id);
    }
    auto tree=entries.empty() ? nullptr : std::make_unique<Tree>(entries.begin(),entries.end());
    std::vector<Id> hits;
    return measure<3>(data,false,verify,elapsed(start),[&](const Query<3>& q) {
        hits.clear();
        if (tree) {
            auto out=std::back_inserter(hits);
            if (q.radius>>64) tree->queryDisk(IndexiconSphere<true>{Ball<3,true>(q.point,q.radius)},out);
            else tree->queryDisk(IndexiconSphere<false>{Ball<3,false>(q.point,q.radius)},out);
        }
        return std::span<const Id>(hits);
    },[](Id id){return id;});
}

int run_sphere(const Case<3>& data, const std::string& name, bool verify) {
    if (name=="indexicon_kdtree_adaptive") return indexicon_run<KDSplit::ADAPTIVE>(data,verify);
    if (name=="indexicon_kdtree_longest_axis") return indexicon_run<KDSplit::LONGEST_AXIS>(data,verify);
    if (name=="indexicon_kdtree_round_robin") return indexicon_run<KDSplit::ROUND_ROBIN>(data,verify);
    throw std::invalid_argument("Unknown Indexicon backend");
}
#elif defined(FOLLOWUP_PGM)
#include "pgm/pgm_index_variants.hpp"

int run_sphere(const Case<3>& data, const std::string&, bool verify) {
    const auto start=Clock::now();
    using Tree=pgm::MultidimensionalPGMIndex<3,std::uint64_t,64>;
    using Code=mortonnd::MortonNDBmi<3,std::uint64_t>;
    using Key=Tree::value_type;
    constexpr unsigned shift=32-(64/3-1);
    auto cell=[](const Point<3>& p) {return Key(p[0]>>shift,p[1]>>shift,p[2]>>shift);};
    std::vector<Key> keys;
    std::vector<std::pair<std::uint64_t,Id>> order;
    keys.reserve(data.points.size());
    order.reserve(data.points.size());
    for (Id id=0;id<data.points.size();++id) {
        auto key=cell(data.points[id]);
        keys.push_back(key);
        order.emplace_back(std::apply([](auto... x){return Code::Encode(x...);},key),id);
    }
    std::sort(order.begin(),order.end());
    struct Entry {Point<3> point; Id id;};
    std::vector<Entry> candidates;
    candidates.reserve(order.size());
    for (const auto& entry:order) candidates.push_back({data.points[entry.second],entry.second});
    auto tree=keys.empty() ? nullptr : std::make_unique<Tree>(keys.begin(),keys.end());
    std::vector<Id> hits;
    return measure<3>(data,false,verify,elapsed(start),[&](const Query<3>& q) {
        hits.clear();
        auto scan=[&](const auto& ball) {
            for (auto it=tree->range(cell(ball.box.low),cell(ball.box.high));it!=tree->end();++it) {
                const auto& entry=candidates[it.source_position()];
                if (ball.contains(entry.point)) hits.push_back(entry.id);
            }
        };
        if (tree) {
            if (q.radius>>64) scan(Ball<3,true>(q.point,q.radius));
            else scan(Ball<3,false>(q.point,q.radius));
        }
        return std::span<const Id>(hits);
    },[](Id id){return id;});
}
#elif defined(FOLLOWUP_LSI)
#include <spatialindex/SpatialIndex.h>

struct SpatialStream : SpatialIndex::IDataStream {
    const std::vector<Point<3>>& points;
    Id next=0;
    explicit SpatialStream(const std::vector<Point<3>>& input) : points(input) {}
    SpatialIndex::IData* getNext() override {
        if (!hasNext()) return nullptr;
        const auto& p=points[next];
        const double coords[]{double(p[0]),double(p[1]),double(p[2])};
        SpatialIndex::Region bounds(coords,coords,3);
        return new SpatialIndex::RTree::Data(0,nullptr,bounds,next++);
    }
    bool hasNext() override {return next<points.size();}
    std::uint32_t size() override {return points.size();}
    void rewind() override {next=0;}
};
template<bool WideRadius> struct SpatialSphere : SpatialIndex::Region {
    Ball<3,WideRadius> ball;
    explicit SpatialSphere(const Query<3>& q) : ball(q.point,q.radius) {makeDimension(3);}
    bool intersectsRegion(const SpatialIndex::Region& bounds) const override {
        Box<3> box;
        for(unsigned a=0;a<3;++a){box.low[a]=bounds.m_pLow[a];box.high[a]=bounds.m_pHigh[a];}
        return ball.intersects(box);
    }
};
struct SpatialVisitor : SpatialIndex::IVisitor {
    std::vector<Id> hits;
    void visitNode(const SpatialIndex::INode&) override {}
    void visitData(const SpatialIndex::IData& data) override {hits.push_back(data.getIdentifier());}
    void visitData(std::vector<const SpatialIndex::IData*>& rows) override {for(auto* row:rows)visitData(*row);}
};

int run_sphere(const Case<3>& data, const std::string& name, bool verify) {
    using namespace SpatialIndex;
    const auto start=Clock::now();
    auto variant=name=="lsi_linear" ? RTree::RV_LINEAR :
        name=="lsi_quadratic" ? RTree::RV_QUADRATIC : RTree::RV_RSTAR;
    std::unique_ptr<IStorageManager> storage(StorageManager::createNewMemoryStorageManager());
    id_type root;
    SpatialStream stream(data.points);
    std::unique_ptr<ISpatialIndex> tree(name=="lsi_str" && !data.points.empty()
        ? RTree::createAndBulkLoadNewRTree(RTree::BLM_STR,stream,*storage,.7,16,16,3,variant,root)
        : RTree::createNewRTree(*storage,variant==RTree::RV_RSTAR?.7:.5,16,16,3,variant,root));
    if (name!="lsi_str") for (Id id=0;id<data.points.size();++id) {
        const auto& p=data.points[id];
        const double coords[]{double(p[0]),double(p[1]),double(p[2])};
        tree->insertData(0,nullptr,Region(coords,coords,3),id);
    }
    SpatialVisitor visitor;
    return measure<3>(data,false,verify,elapsed(start),[&](const Query<3>& q) {
        visitor.hits.clear();
        if (q.radius>>64) tree->intersectsWithQuery(SpatialSphere<true>(q),visitor);
        else tree->intersectsWithQuery(SpatialSphere<false>(q),visitor);
        return std::span<const Id>(visitor.hits);
    },[](Id id){return id;});
}
#elif defined(FOLLOWUP_CGAL)
#include <CGAL/Simple_cartesian.h>
#include <CGAL/Search_traits_3.h>
#include <CGAL/Search_traits_adapter.h>
#include <CGAL/property_map.h>
#include <CGAL/Kd_tree.h>

using Kernel=CGAL::Simple_cartesian<double>;
using Entry=std::pair<Kernel::Point_3,Id>;
using Traits=CGAL::Search_traits_adapter<Entry,CGAL::First_of_pair_property_map<Entry>,CGAL::Search_traits_3<Kernel>>;

template<bool WideRadius> struct CgalSphere {
    Ball<3,WideRadius> ball;
    bool contains(const Entry& entry) const {
        const auto& p=entry.first;
        return ball.contains(Point<3>{Coord(p.x()),Coord(p.y()),Coord(p.z())});
    }
    template<class Rectangle> auto box(const Rectangle& rectangle) const {
        Box<3> bounds;
        for(unsigned a=0;a<3;++a){
            bounds.low[a]=std::floor(rectangle.min_coord(a));
            bounds.high[a]=std::ceil(rectangle.max_coord(a));
        }
        return bounds;
    }
    bool inner_range_intersects(const auto& bounds) const {return ball.intersects(box(bounds));}
    bool outer_range_contains(const auto& bounds) const {return ball.classify(box(bounds))==Relation::inside;}
};

int run_sphere(const Case<3>& data, const std::string&, bool verify) {
    const auto start=Clock::now();
    std::vector<Entry> entries;
    entries.reserve(data.points.size());
    for (Id id=0;id<data.points.size();++id) {
        const auto& p=data.points[id];
        entries.emplace_back(Kernel::Point_3(p[0],p[1],p[2]),id);
    }
    CGAL::Kd_tree<Traits> tree(entries.begin(),entries.end());
    if (!entries.empty()) tree.build();
    std::vector<Entry> hits;
    return measure<3>(data,false,verify,elapsed(start),[&](const Query<3>& q) {
        hits.clear();
        if (!entries.empty()) {
            auto out=std::back_inserter(hits);
            if (q.radius>>64) tree.search(out,CgalSphere<true>{Ball<3,true>(q.point,q.radius)});
            else tree.search(out,CgalSphere<false>{Ball<3,false>(q.point,q.radius)});
        }
        return std::span<const Entry>(hits);
    },[](const Entry& entry){return entry.second;});
}
#endif
