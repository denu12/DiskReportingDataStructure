#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

using Wide = unsigned __int128;
using Coord = std::uint32_t;
using Id = std::size_t;
template<unsigned D> using Point = std::array<Coord,D>;

enum class Relation { outside, crossing, inside };

template<unsigned D> struct Box {
    Point<D> low, high;
    bool contains(const auto& p) const {
        for (unsigned a=0; a<D; ++a)
            if (p[a]<low[a] || p[a]>high[a]) return false;
        return true;
    }
};

template<unsigned D, bool WideRadius> struct Ball {
    Point<D> center;
    Wide radius;
    Box<D> box;

    Ball(Point<D> c, Wide squared) : center(c), radius(squared) {
        constexpr std::uint64_t max=UINT32_MAX;
        auto r=max;
        if (squared < Wide(max)*max) {
            r=std::uint64_t(std::sqrt(double(squared)));
            if (Wide(r)*r > squared) --r;
            if (Wide(r+1)*(r+1) <= squared) ++r;
        }
        for (unsigned a=0; a<D; ++a) {
            box.low[a]=center[a] < r ? 0 : center[a]-r;
            box.high[a]=std::min(max,center[a]+r);
        }
    }

    static std::uint64_t square_delta(Coord a, Coord b) {
        const auto delta=std::uint64_t(a)-b;
        return delta*delta;
    }

    bool contains(const auto& p) const {
        if constexpr (WideRadius) {
            Wide sum=0;
            for (unsigned a=0; a<D; ++a) sum+=square_delta(p[a],center[a]);
            return sum<=radius;
        } else {
            std::uint64_t sum=0, overflow=0;
            for (unsigned a=0; a<D; ++a) {
                const auto term=square_delta(p[a],center[a]);
                sum+=term;
                if (a) overflow |= sum<term;
            }
            return (sum<=std::uint64_t(radius)) & !overflow;
        }
    }

    bool intersects(const Box<D>& bounds) const {
        Point<D> nearest;
        for (unsigned a=0; a<D; ++a)
            nearest[a]=std::clamp(center[a],bounds.low[a],bounds.high[a]);
        return contains(nearest);
    }

    Relation classify(const Box<D>& bounds) const {
        if (!intersects(bounds)) return Relation::outside;
        Point<D> farthest;
        for (unsigned a=0; a<D; ++a) {
            const auto lo=std::int64_t(center[a])-bounds.low[a];
            const auto hi=std::int64_t(bounds.high[a])-center[a];
            farthest[a]=lo>hi ? bounds.low[a] : bounds.high[a];
        }
        return contains(farthest) ? Relation::inside : Relation::crossing;
    }
};

#if defined(FOLLOWUP_PH)
#include "phtree/phtree_multimap.h"

template<unsigned D, bool WideRadius>
struct PhFilter : improbable::phtree::FilterNoOp {
    const Ball<D,WideRadius>& ball;
    explicit PhFilter(const Ball<D,WideRadius>& query) : ball(query) {}

    template<class Key, class Bucket>
    bool IsEntryValid(const Key& point, const Bucket&) const { return ball.contains(point); }

    template<class Key>
    bool IsNodeValid(const Key& prefix, int bits) const {
        if (bits >= 32) return true;
        const auto mask=(std::uint32_t(1)<<bits)-1;
        Box<D> box;
        for (unsigned a=0; a<D; ++a) {
            box.low[a]=Coord(prefix[a])&~mask;
            box.high[a]=Coord(prefix[a])|mask;
        }
        return ball.intersects(box);
    }
};
#elif defined(FOLLOWUP_PSI)
struct PsiCube {
    Point<3> low, high;
    Point<3> width;

    PsiCube(Point<3> lo, Point<3> hi) : low(lo), high(hi) {
        for (unsigned a=0; a<3; ++a) width[a]=hi[a]-lo[a];
    }
    bool contains(const auto& p) const {
        // Unsigned subtraction combines the inclusive lower and upper tests.
        bool inside=true;
        for (unsigned a=0; a<3; ++a) inside &= Coord(p[a]-low[a])<=width[a];
        return inside;
    }
    Relation classify(const auto& box) const {
        bool overlaps=true, inside=true;
        for (unsigned a=0; a<3; ++a) {
            overlaps &= (box.first[a]<=high[a]) & (box.second[a]>=low[a]);
            inside &= (box.first[a]>=low[a]) & (box.second[a]<=high[a]);
        }
        return !overlaps ? Relation::outside : inside ? Relation::inside : Relation::crossing;
    }
};

template<class Traits, class P, class Shape>
bool psi_disk_point(const P& p, const Shape& query) {
    if constexpr (requires { query.contains(p); }) return query.contains(p);
    else return Traits::within_box(p,query);
}
template<class Traits, class B, class Shape>
Relation psi_disk_classify(const B& b, const Shape& query) {
    if constexpr (requires { query.radius; }) {
        Box<std::tuple_size_v<decltype(query.center)>> bounds;
        for (unsigned a=0; a<bounds.low.size(); ++a) {
            bounds.low[a]=std::clamp<std::int64_t>(b.first[a],0,UINT32_MAX);
            bounds.high[a]=std::clamp<std::int64_t>(b.second[a],0,UINT32_MAX);
        }
        return query.classify(bounds);
    } else if constexpr (std::is_same_v<Shape,PsiCube>) return query.classify(b);
    else if (!Traits::box_intersect_box(b,query)) return Relation::outside;
    else return Traits::within_box(b,query) ? Relation::inside : Relation::crossing;
}
template<class Traits, class Shape> bool psi_disk_empty(const Shape& query) {
    if constexpr (requires { query.radius; } || std::is_same_v<Shape,PsiCube>) return false;
    else return Traits::box_is_empty(query);
}

#include "psi/kd_tree.h"
#include "psi/orth_tree.h"
#include "psi/p_tree.h"
#include "psi/dependence/splitter.h"

struct PsiId {
    using id_type=Id;
    using curve_code_type=std::uint64_t;
    curve_code_type code=0;
    id_type id=0;
    void set_member(curve_code_type value) { code=value; }
    bool operator<(const PsiId& rhs) const { return code==rhs.code ? id<rhs.id : code<rhs.code; }
    bool operator==(const PsiId& rhs) const { return id==rhs.id; }
    friend std::ostream& operator<<(std::ostream& out, const PsiId& value) { return out<<value.id; }
};
#endif

template<class T> T read(std::istream& in) {
    T v{};
    if (!in.read(reinterpret_cast<char*>(&v),sizeof(v))) throw std::runtime_error("Truncated input");
    return v;
}
template<unsigned D> struct Query { Point<D> point, high; Wide radius; };
template<unsigned D> struct Case {
    std::vector<Point<D>> points;
    std::vector<Query<D>> queries;
};
template<unsigned D> Case<D> load(std::istream& in, bool box) {
    Case<D> data;
    auto n=read<std::uint64_t>(in), q=read<std::uint64_t>(in);
    data.points.resize(n);
    static_assert(sizeof(Point<D>)==D*sizeof(Coord));
    if (n && !in.read(reinterpret_cast<char*>(data.points.data()),n*sizeof(Point<D>)))
        throw std::runtime_error("Truncated points");
    data.queries.resize(q);
    for (auto& query : data.queries) {
        query.point=read<Point<D>>(in);
        if (box) query.high=read<Point<D>>(in);
        else {
            query.radius=read<std::uint64_t>(in);
            query.radius|=Wide(read<std::uint64_t>(in))<<64;
        }
    }
    if (in.peek()!=EOF) throw std::runtime_error("Trailing input bytes");
    return data;
}

using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point start) { return std::chrono::duration<double>(Clock::now()-start).count(); }

template<unsigned D, class Search, class IdOf>
int measure(const Case<D>& data, bool box, bool verify, double build, Search search, IdOf id_of) {
    std::size_t answers=0;
    double query_seconds=0;
    const auto batch=Clock::now();
    for (const auto& q : data.queries) {
        const auto start=verify ? Clock::now() : batch;
        const auto hits=search(q);
        asm volatile("" : : "r"(hits.data()), "r"(hits.size()) : "memory");
        answers+=hits.size();
        if (!verify) continue;
        query_seconds+=elapsed(start);
        std::vector<Id> expected, actual;
        for (Id id=0; id<data.points.size(); ++id) {
            if (box) {
                if (Box<D>{q.point,q.high}.contains(data.points[id])) expected.push_back(id);
            } else {
                Wide squared=0;
                for (unsigned a=0; a<D; ++a) {
                    const auto delta=__int128(data.points[id][a])-q.point[a];
                    squared+=Wide(delta*delta);
                }
                if (squared<=q.radius) expected.push_back(id);
            }
        }
        for (const auto& hit : hits) actual.push_back(id_of(hit));
        std::sort(actual.begin(),actual.end());
        if (actual!=expected) {
            std::cerr<<"Incorrect result for query "<<(&q-data.queries.data())<<'\n';
            return 2;
        }
    }
    if (!verify) query_seconds=elapsed(batch);
    std::cout<<"{\"status\":\"success\",\"dimension\":"<<D<<",\"queries\":"<<data.queries.size()
             <<",\"answers\":"<<answers<<",\"build_seconds\":"<<build
             <<",\"query_seconds\":"<<query_seconds<<"}\n";
    return 0;
}

#if defined(FOLLOWUP_INDEXICON) || defined(FOLLOWUP_PGM) || defined(FOLLOWUP_LSI) || defined(FOLLOWUP_CGAL)
#include "other_disk_3d.h"
#endif

#if defined(FOLLOWUP_PSI)
template<unsigned D,class P,class Tree,bool Spac=false>
int run_psi(const Case<D>& data, bool box, bool verify) {
    const auto start=Clock::now();
    parlay::sequence<P> points(data.points.size()), out(data.points.size());
    for (Id i=0;i<points.size();++i) {
        for (unsigned a=0;a<D;++a) points[i][a]=data.points[i][a];
        points[i].aug.id=i;
    }
    Tree tree;
    if (!points.empty()) tree.build(parlay::make_slice(points));
    return measure<D>(data,box,verify,elapsed(start),[&](const Query<D>& q) {
        if (points.empty()) return std::span<const P>{};
        auto report=[&](const auto& shape){return tree.range_query(shape,parlay::make_slice(out)).first;};
        std::size_t count;
        if (box) {
            if constexpr (Spac && D==3) count=report(PsiCube(q.point,q.high));
            else {
                typename Tree::box_type bounds;
                for(unsigned a=0;a<D;++a){bounds.first[a]=q.point[a];bounds.second[a]=q.high[a];}
                count=report(bounds);
            }
        } else if (q.radius>>64) count=report(Ball<D,true>(q.point,q.radius));
        else count=report(Ball<D,false>(q.point,q.radius));
        return std::span<const P>(out.data(),count);
    },[](const P& p){return p.aug.id;});
}
#endif

template<unsigned D>
int run(const Case<D>& data, const std::string& algorithm, bool box, bool verify) {
#if defined(FOLLOWUP_PH)
    if (algorithm!="phtree") throw std::invalid_argument("Unknown PH-tree backend");
    const auto start=Clock::now();
    using Tree=improbable::phtree::PhTreeMultiMap<D,Id>;
    using Key=improbable::phtree::PhPoint<D>;
    Tree tree;
    auto key=[](const Point<D>& point) {
        Key k;
        std::copy(point.begin(),point.end(),k.begin());
        return k;
    };
    for (Id id=0;id<data.points.size();++id) tree.emplace(key(data.points[id]),id);
    std::vector<Id> hits;
    return measure<D>(data,box,verify,elapsed(start),[&](const Query<D>& q) {
        hits.clear();
        auto emit=[&](const auto&,Id id){hits.push_back(id);};
        if (box) tree.for_each({key(q.point),key(q.high)},emit);
        else {
            auto report=[&]<bool wide>(const Ball<D,wide>& ball) {
                tree.for_each({key(ball.box.low),key(ball.box.high)},emit,PhFilter<D,wide>(ball));
            };
            if (q.radius>>64) report(Ball<D,true>(q.point,q.radius));
            else report(Ball<D,false>(q.point,q.radius));
        }
        return std::span<const Id>(hits);
    },[](Id id){return id;});
#elif defined(FOLLOWUP_PSI)
    using P=psi::aug_point<std::int64_t,D,PsiId>;
    using B=psi::point_traits<P>;
    using K=psi::orthogonal_split_rule<psi::max_stretch_dim<P>,psi::object_median<P>>;
    using O=psi::orthogonal_split_rule<psi::rotate_dim<P>,psi::spatial_median<P>>;
    using Z=psi::spatial_filling_curve<psi::morton_curve<P>>;
    using H=psi::spatial_filling_curve<psi::hilbert_curve<P>>;
    if (algorithm=="psi_kd") return run_psi<D,P,psi::kd_tree<psi::tree_traits<P,K>>>(data,box,verify);
    if (algorithm=="psi_orth") return run_psi<D,P,psi::orth_tree<psi::orth_tree_traits<P,O,
        psi::box_leaf_aug<B>,psi::box_interior_aug<B>>>>(data,box,verify);
    if (algorithm=="psi_spac_z") return run_psi<D,P,psi::p_tree<psi::tree_traits<P,Z>>,true>(data,box,verify);
    if (algorithm=="psi_spac_h") return run_psi<D,P,psi::p_tree<psi::tree_traits<P,H>>,true>(data,box,verify);
    throw std::invalid_argument("Unknown PSI backend");
#else
    if constexpr (D==3) {
        if (box) throw std::invalid_argument("This runner expects sphere inputs");
        return run_sphere(data,algorithm,verify);
    }
    throw std::invalid_argument("This runner expects 3D inputs");
#endif
}

int main(int argc,char** argv) {
    try {
        if (argc!=3 && (argc!=4 || std::string(argv[3])!="--bench"))
            throw std::invalid_argument("Usage: runner FILE ALGORITHM [--bench]");
        std::ifstream in(argv[1],std::ios::binary);
        const auto header=read<std::array<char,8>>(in);
        const bool box=header==std::array<char,8>{'S','Q','U','A','R','E','1','\0'};
        unsigned dimension=2;
        if (box) dimension=read<unsigned>(in);
        else if (header!=std::array<char,8>{'E','S','A','2','D','0','1','\0'}) {
            in.seekg(0);
            dimension=read<unsigned>(in);
            if (dimension!=3) throw std::invalid_argument("Expected a 2D or 3D benchmark input");
        }
        if (dimension==2) return run<2>(load<2>(in,box),argv[2],box,argc==3);
        if (dimension==3) return run<3>(load<3>(in,box),argv[2],box,argc==3);
        throw std::invalid_argument("Unsupported dimension");
    } catch (const std::exception& error) {
        std::cerr<<error.what()<<'\n';
        return 1;
    }
}
