// Compile each upstream header separately: their global type names overlap.
#include <cfloat>
#include <iterator>
#include <type_traits>
#include <utility>
#if defined(INDEXICON_DISK_TRAVERSAL)
#include "disk_geometry_2d.h"
#endif
#if defined(INDEXICON_RTREE_POINT)
#include "rtree_point.hpp"
#elif defined(INDEXICON_RTREE_MBR)
#include "rtree_mbr.hpp"
#elif defined(INDEXICON_KDTREE)
#include "kdtree.hpp"
#elif defined(INDEXICON_QUADTREE)
#include "quadtree.hpp"
#elif defined(INDEXICON_MXCIF)
#include "mxcif_quadtree.hpp"
#elif defined(INDEXICON_OCTREE)
#include "octtree.hpp"
#endif

const char* output_contract = "point_ids_only";
const char* output_representation = "indexicon_value_ids";
#if defined(INDEXICON_DISK_TRAVERSAL)
const char* membership_contract = "closed_integer_ball";
#else
const char* membership_contract = "original_box_api_with_integer_ball_filter";
#endif

namespace indexicon_adapter {
using Id = std::size_t;
using Coord = double;
// Binary scaling preserves every uint32 coordinate exactly in double.
Coord coord(std::uint64_t x) { return std::ldexp(Coord(x), -32); }

template<std::size_t D>
struct Candidate {
    Id id{};
    std::array<std::uint32_t,D> coords{};
};

template<std::size_t D>
#if defined(INDEXICON_DISK_TRAVERSAL)
using Value = Id;
#else
using Value = std::conditional_t<(D <= 3), Candidate<D>, Id>;
#endif

template<std::size_t D>
Value<D> value(Id id, const Point& p) {
#if defined(INDEXICON_DISK_TRAVERSAL)
    return id;
#else
    if constexpr (D <= 3) {
        Candidate<D> c;
        c.id = id;
        std::copy_n(p.begin(), D, c.coords.begin());
        return c;
    } else {
        return id;
    }
#endif
}

#if defined(INDEXICON_DISK_TRAVERSAL)
struct NativeDisk {
    Disk2D disk;

    static double unscale(double x) {
        return std::clamp(x * 4294967296., 0., double(UINT32_MAX));
    }

    bool contains(double x, double y) const {
        // Stored points are exact binary-scaled uint32 coordinates.
        return disk.contains(x * 4294967296., y * 4294967296.);
    }

    bool intersects(double x0, double y0, double x1, double y1) const {
        return disk.intersects({std::uint32_t(unscale(x0)), std::uint32_t(unscale(y0))},
            {std::uint32_t(std::ceil(unscale(x1))), std::uint32_t(std::ceil(unscale(y1)))});
    }

    bool covers(double x0, double y0, double x1, double y1) const {
        return disk.covers({std::uint32_t(unscale(x0)), std::uint32_t(unscale(y0))},
            {std::uint32_t(std::ceil(unscale(x1))), std::uint32_t(std::ceil(unscale(y1)))});
    }
};
#endif

// Filter while the native range traversal emits each candidate. The coordinates
// travel with the ID, so the timed path never gathers from the input point array.
template<std::size_t D>
struct DiskOutput {
    std::vector<Id>& hits;
    const std::array<std::uint32_t,D>& center;
    Wide radius2;
    DiskOutput& operator*() { return *this; }
    DiskOutput& operator++() { return *this; }
    DiskOutput operator++(int) { return *this; }
    void operator=(const Candidate<D>& candidate) {
        Wide sum = 0;
        for (Id a = 0; a < D; ++a) {
            // The signed difference's magnitude is at most UINT32_MAX. Its
            // square therefore fits in uint64, including after modular subtraction.
            const auto diff = std::uint64_t(candidate.coords[a]) - center[a];
            sum += diff * diff;
        }
        if (sum <= radius2) hits.push_back(candidate.id);
    }
};

template<std::size_t D>
auto bounds(const Data& data, Id q) {
    constexpr auto max = std::uint64_t(UINT32_MAX);
    const auto radius2 = data.radii[q];
    auto radius = max;
    if (radius2 < Wide(max) * max) {
        radius = std::uint64_t(std::sqrt(double(radius2)));
        // The floating estimate seeds the search; these checks establish the
        // exact integer floor even on perfect-square and full-width boundaries.
        while (Wide(radius) * radius > radius2) --radius;
        while (Wide(radius+1) * (radius+1) <= radius2) ++radius;
    }
    std::array<Coord, D> lower{}, upper{};
    for (Id a = 0; a < D; ++a) {
        const auto c = std::uint64_t(data.centers[q][a]);
        lower[a] = coord(c > radius ? c - radius : 0);
        upper[a] = coord(std::min(max, c + radius));
    }
    return std::pair{lower, upper};
}

template<std::size_t D, class Tree, class Entry, class Box>
Query make(Data& data, Entry entry, Box box) {
    using Record = decltype(entry(Id{}, std::declval<const Point&>()));
    std::vector<Record> entries;
    entries.reserve(data.points.size());
    for (Id i = 0; i < data.points.size(); ++i) entries.push_back(entry(i, data.points[i]));
    // Some upstream bulk-load constructors require at least one record.
    auto tree = entries.empty() ? std::shared_ptr<Tree>{} :
        std::make_shared<Tree>(entries.begin(), entries.end());
    auto hits = std::make_shared<std::vector<Id>>();
    return {
        [&, tree, hits, box](Id q) {
            hits->clear();
            if (!tree) return;
#if defined(INDEXICON_DISK_TRAVERSAL)
            static_assert(D == 2);
            tree->queryDisk(NativeDisk{Disk2D(data.centers[q], data.radii[q])}, std::back_inserter(*hits));
#else
            auto [lo, hi] = bounds<D>(data, q);
            if constexpr (D <= 3) {
                std::array<std::uint32_t,D> center;
                std::copy_n(data.centers[q].begin(), D, center.begin());
                tree->query(box(lo, hi), DiskOutput<D>{*hits, center, data.radii[q]});
            } else {
                tree->query(box(lo, hi), std::back_inserter(*hits));
                std::erase_if(*hits, [&](Id id) { return !data.contains(id, q); });
            }
#endif
            asm volatile("" :: "r"(hits->data()), "r"(hits->size()) : "memory");
        },
        [hits] { return hits->size(); },
        [&, hits](Id q) { return verify_ids(data, q, *hits); }
    };
}

#if defined(INDEXICON_RTREE_POINT) || defined(INDEXICON_RTREE_MBR) || defined(INDEXICON_KDTREE)
template<std::size_t D>
Query dimensional(Data& data, const std::string& algorithm) {
#if defined(INDEXICON_KDTREE)
    using P = KDPoint<Coord, D>;
    auto entry = [](Id id, const Point& p) {
        P value;
        for (Id a = 0; a < D; ++a) value[a] = coord(p[a]);
        return std::pair{value, indexicon_adapter::value<D>(id, p)};
    };
    auto box = [](const auto& lo, const auto& hi) {
        KDRegion<Coord, D> b; b.low.coords = lo; b.high.coords = hi; return b;
    };
    if (algorithm == "indexicon_kdtree_adaptive")
        return make<D, KDTree<Coord, Value<D>, D, 128, KDSplit::ADAPTIVE>>(data, entry, box);
    if (algorithm == "indexicon_kdtree_round_robin")
        return make<D, KDTree<Coord, Value<D>, D, 128, KDSplit::ROUND_ROBIN>>(data, entry, box);
    if (algorithm == "indexicon_kdtree_longest_axis")
        return make<D, KDTree<Coord, Value<D>, D, 128, KDSplit::LONGEST_AXIS>>(data, entry, box);
#else
    using Tree = RTree<Value<D>, Coord, D>;
    using P = RPoint<Coord, D>;
    using Box = RBox<Coord, D>;
    auto entry = [](Id id, const Point& p) {
        P value;
        for (Id a = 0; a < D; ++a) value[a] = coord(p[a]);
#if defined(INDEXICON_RTREE_POINT)
        return std::pair{value, indexicon_adapter::value<D>(id, p)};
#else
        return std::pair{Box(value, value), indexicon_adapter::value<D>(id, p)};
#endif
    };
    auto box = [](const auto& lo, const auto& hi) {
        P lower, upper; lower.coords = lo; upper.coords = hi; return Box(lower, upper);
    };
#if defined(INDEXICON_RTREE_POINT)
    if (algorithm == "indexicon_rtree_point") return make<D, Tree>(data, entry, box);
#else
    if (algorithm == "indexicon_rtree_mbr") return make<D, Tree>(data, entry, box);
#endif
#endif
    throw std::invalid_argument("Unknown Indexicon algorithm: " + algorithm);
}

template<std::size_t... D>
Query dispatch(Data& data, const std::string& algorithm, std::index_sequence<D...>) {
    Query result;
    if (((data.d == D && (result = dimensional<D>(data, algorithm), true)) || ...)) return result;
    throw std::invalid_argument("Dimension is not compiled for Indexicon");
}
#endif
} // namespace indexicon_adapter

Query create(Data& data, const std::string& algorithm) {
    using namespace indexicon_adapter;
#if defined(INDEXICON_QUADTREE)
    if (data.d != 2) throw std::invalid_argument("Indexicon quadtree requires 2D");
    using V = Value<2>;
    auto entry = [](Id id, const Point& p) { return QPoint<Coord, V>(value<2>(id, p), coord(p[0]), coord(p[1])); };
    auto box = [](const auto& lo, const auto& hi) { return QBox<Coord, V>(lo[0], lo[1], hi[0], hi[1], V{}); };
    if (algorithm == "indexicon_quadtree_pr")
        return make<2, QuadTreeNode<Coord, V, 128, SplitStrategy::PR>>(data, entry, box);
    if (algorithm == "indexicon_quadtree_pseudo_median")
        return make<2, QuadTreeNode<Coord, V, 128, SplitStrategy::PSEUDO_MEDIAN>>(data, entry, box);
    if (algorithm == "indexicon_quadtree_longest_axis")
        return make<2, QuadTreeNode<Coord, V, 128, SplitStrategy::POINT_LONGEST_AXIS>>(data, entry, box);
#elif defined(INDEXICON_MXCIF)
    if (data.d != 2) throw std::invalid_argument("Indexicon MX-CIF quadtree requires 2D");
    using V = Value<2>;
    auto entry = [](Id id, const Point& p) {
        const auto x = coord(p[0]), y = coord(p[1]); return MXCIFBox<Coord, V>(value<2>(id, p), x, y, x, y);
    };
    auto box = [](const auto& lo, const auto& hi) { return MXCIFBox<Coord, V>(V{}, lo[0], lo[1], hi[0], hi[1]); };
    if (algorithm == "indexicon_mxcif_quadtree") return make<2, MXCIFQuadTreeNode<Coord, V>>(data, entry, box);
#elif defined(INDEXICON_OCTREE)
    if (data.d != 3) throw std::invalid_argument("Indexicon octree requires 3D");
    using V = Value<3>;
    auto entry = [](Id id, const Point& p) { return OPoint<Coord, V>(value<3>(id, p), coord(p[0]), coord(p[1]), coord(p[2])); };
    auto box = [](const auto& lo, const auto& hi) { return OBox<Coord, V>(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]); };
    if (algorithm == "indexicon_octree") return make<3, OctreeNode<Coord, V>>(data, entry, box);
#else
    return dispatch(data, algorithm, std::index_sequence<INDEXICON_DIMS>{});
#endif
    throw std::invalid_argument("Unknown Indexicon algorithm: " + algorithm);
}
