#pragma once

const char* membership_contract = "closed_integer_ball";

#if defined(BACKEND_CGAL_RANGE)
#include <CGAL/Simple_cartesian.h>
#include <CGAL/Range_segment_tree_traits.h>
#include <CGAL/Range_tree_k.h>
const char* output_contract = "floating_points";
const char* output_representation = "native_cgal_points";

using Traits = CGAL::Range_segment_tree_set_traits_2<CGAL::Simple_cartesian<double>>;
using NativePoint = Traits::Key;

Query create(Data& data, const std::string&) {
    using Tree = CGAL::Range_tree_2<Traits>;
    std::vector<NativePoint> points;
    points.reserve(data.points.size());
    for (const auto& p : data.points) points.emplace_back(p[0], p[1]);
    auto tree = points.empty() ? nullptr : std::make_shared<Tree>(points.begin(), points.end());
    auto hits = std::make_shared<std::vector<NativePoint>>();
    return {
        [&, tree, hits](std::size_t q) {
            hits->clear();
            if (!tree) return;
            Disk2D disk(data.centers[q], data.radii[q]);
            auto [lo, hi] = disk.bounds();
            tree->window_query(Traits::Interval(NativePoint(lo[0], lo[1]),
                NativePoint(double(hi[0])+1, double(hi[1])+1)), std::back_inserter(*hits));
            std::erase_if(*hits, [&](const auto& p) { return !disk.contains(p.x(),p.y()); });
        },
        [hits] { return hits->size(); },
        [&, hits](std::size_t q) {
            std::vector<CoordinatePair> actual, expected;
            for (const auto& p : *hits) actual.push_back({std::uint32_t(p.x()), std::uint32_t(p.y())});
            for (std::size_t i = 0; i < data.points.size(); ++i)
                if (data.contains(i, q)) expected.push_back({data.points[i][0], data.points[i][1]});
            std::sort(actual.begin(), actual.end());
            std::sort(expected.begin(), expected.end());
            return actual == expected;
        }
    };
}

#elif defined(BACKEND_STREAM_PAM)
#include <pam/pam.h>
#define Point PamPoint
#include "range_utils.h"
#include "range_tree.h"
#undef Point
const char* output_contract = "integer_points";
const char* output_representation = "native_pam_points";

using PamIndex = RangeQuery<std::uint32_t, std::uint32_t>;
struct PamDiskOutput {
    const Disk2D& disk;
    std::uint32_t low, high;
    std::vector<CoordinatePair>& hits;
    void emit(std::uint32_t x, std::uint32_t y, std::uint32_t count) {
        if (disk.contains(x, y)) hits.insert(hits.end(), count, {x, y});
    }
    void add_entry(PamIndex::main_entry entry) {
        const auto [x, y] = entry.first;
        if (low <= y && y <= high) emit(x, y, entry.second);
    }
    void add_aug_val(PamIndex::inner_map map) {
        auto range = PamIndex::inner_map::range(map, {low, 0}, {high, UINT32_MAX});
        PamIndex::inner_map::foreach_index(range, [&](const auto& entry, std::size_t) {
            emit(entry.first.second, entry.first.first, entry.second);
        }, 0, std::numeric_limits<std::size_t>::max());
    }
};

Query create(Data& data, const std::string&) {
    if (!data.points.empty()) PamIndex::reserve(data.points.size());
    auto entries = parlay::tabulate(data.points.size(), [&](std::size_t i) -> PamIndex::main_entry {
        return {{data.points[i][0], data.points[i][1]}, 1};
    });
    auto index = std::make_shared<PamIndex::outer_map>(entries,
        [](std::uint32_t a, std::uint32_t b) { return a + b; });
    auto hits = std::make_shared<std::vector<CoordinatePair>>();
    return {
        [&, index, hits](std::size_t q) {
            hits->clear();
            const Disk2D disk(data.centers[q], data.radii[q]);
            const auto [lo, hi] = disk.bounds();
            PamDiskOutput output{disk, lo[1], hi[1], *hits};
            index->range_sum({lo[0], 0}, {hi[0], UINT32_MAX}, output);
        },
        [hits] { return hits->size(); },
        [&, hits](std::size_t q) {
            auto actual = *hits;
            std::vector<CoordinatePair> expected;
            for (std::size_t i=0; i<data.points.size(); ++i)
                if (data.contains(i,q)) expected.push_back({data.points[i][0], data.points[i][1]});
            std::sort(actual.begin(),actual.end());
            std::sort(expected.begin(),expected.end());
            return actual == expected;
        }
    };
}

#elif defined(BACKEND_EXACT_PARGEO)
#include "pargeo/kdTree.h"
const char* output_contract = "integer_points";
const char* output_representation = "native_pargeo_points";
using ParGeoPoint = pargeo::_point<2, double, pargeo::_empty, pargeo::_empty>;
using ParGeoNode = pargeo::kdNode<2, ParGeoPoint>;

void pargeo_report(ParGeoNode& node, const Disk2D& disk, std::vector<ParGeoPoint>& hits) {
    const auto low = node.getMin(), high = node.getMax();
    CoordinatePair lo{std::uint32_t(low.x[0]), std::uint32_t(low.x[1])};
    CoordinatePair hi{std::uint32_t(high.x[0]), std::uint32_t(high.x[1])};
    if (!disk.intersects(lo, hi)) return;
    if (disk.covers(lo, hi)) {
        for (std::size_t i=0; i<node.size(); ++i) hits.push_back(*node.getItem(i));
    } else if (node.isLeaf()) {
        for (std::size_t i=0; i<node.size(); ++i) {
            const auto& p = *node.getItem(i);
            if (disk.contains(p.x[0], p.x[1])) hits.push_back(p);
        }
    } else {
        pargeo_report(*node.L(), disk, hits);
        pargeo_report(*node.R(), disk, hits);
    }
}

Query create(Data& data, const std::string&) {
    auto points = std::make_shared<parlay::sequence<ParGeoPoint>>(
        parlay::tabulate(data.points.size(), [&](std::size_t i) {
            double p[]{double(data.points[i][0]), double(data.points[i][1])};
            return ParGeoPoint(p);
        }));
    auto items = std::make_shared<parlay::sequence<ParGeoPoint*>>(points->size());
    auto tree = std::shared_ptr<ParGeoNode>(points->empty() ? nullptr :
        pargeo::buildKdt<2>(*points, false, false, items.get()), &std::free);
    auto hits = std::make_shared<std::vector<ParGeoPoint>>();
    return {
        [&, points, items, tree, hits](std::size_t q) {
            hits->clear();
            if (tree) pargeo_report(*tree, Disk2D(data.centers[q], data.radii[q]), *hits);
        },
        [hits] { return hits->size(); },
        [&, hits](std::size_t q) {
            std::vector<CoordinatePair> actual, expected;
            for (const auto& p : *hits) actual.push_back({std::uint32_t(p.x[0]), std::uint32_t(p.x[1])});
            for (std::size_t i=0; i<data.points.size(); ++i)
                if (data.contains(i,q)) expected.push_back({data.points[i][0], data.points[i][1]});
            std::sort(actual.begin(),actual.end());
            std::sort(expected.begin(),expected.end());
            return actual == expected;
        }
    };
}

#elif defined(BACKEND_THST)
#include "THST/QuadTree.h"
#include "THST/RTree.h"
const char* output_contract = "point_ids_only";
const char* output_representation = "native_thst_records";

struct ThstPoint {
    using ElementType = std::int64_t;
    std::int64_t min[2]{};
    std::size_t id{};
    bool operator==(const ThstPoint& other) const { return id == other.id; }
    bool operator<(const ThstPoint& other) const { return id < other.id; }
    explicit operator spatial::BoundingBox<std::int64_t,2>() const { return {min, min}; }
};
struct ThstIndexable {
    const std::int64_t* min(const ThstPoint& p) const { return p.min; }
    const std::int64_t* max(const ThstPoint& p) const { return p.min; }
};
struct ThstDiskPredicate {
    using Box = spatial::BoundingBox<std::int64_t,2>;
    struct DiskBounds : Box {
        Disk2D disk;
        DiskBounds(Disk2D query, const std::int64_t* low, const std::int64_t* high)
            : Box(low, high), disk(query) {}
        bool overlaps(const Box& node) const {
            // Loose quadtree bounds can extend past the data's coordinate domain.
            const auto x = std::clamp<std::int64_t>(disk.center[0], node.min[0], node.max[0]);
            const auto y = std::clamp<std::int64_t>(disk.center[1], node.min[1], node.max[1]);
            if (x < 0 || x > UINT32_MAX || y < 0 || y > UINT32_MAX) return false;
            return disk.contains(x, y);
        }
    } bbox;
    bool operator()(const Box& point) const { return bbox.disk.contains(point.min[0], point.min[1]); }
};

template<class Tree>
Query thst_query(Data& data, std::shared_ptr<Tree> tree) {
    auto hits = std::make_shared<std::vector<ThstPoint>>();
    return {
        [&, tree, hits](std::size_t q) {
            hits->clear();
            if (!tree) return;
            Disk2D disk(data.centers[q], data.radii[q]);
            auto [lo, hi] = disk.bounds();
            const std::int64_t lower[]{lo[0],lo[1]}, upper[]{hi[0],hi[1]};
            tree->query(ThstDiskPredicate{{disk,lower,upper}}, std::back_inserter(*hits));
        },
        [hits] { return hits->size(); },
        [&, hits](std::size_t q) {
            std::vector<std::size_t> ids;
            for (const auto& p : *hits) ids.push_back(p.id);
            return verify_ids(data, q, std::move(ids));
        }
    };
}

Query create(Data& data, const std::string& algorithm) {
    std::vector<ThstPoint> points;
    points.reserve(data.points.size());
    for (const auto& p : data.points) points.push_back({{p[0],p[1]},points.size()});
    if (algorithm == "thst_quad") {
        using Tree = spatial::QuadTree<std::int64_t,ThstPoint,2,ThstIndexable>;
        const std::int64_t lo[]{0,0}, hi[]{UINT32_MAX,UINT32_MAX};
        return thst_query(data, points.empty() ? nullptr :
            std::make_shared<Tree>(lo,hi,points.begin(),points.end()));
    }
    using Tree = spatial::RTree<std::int64_t,ThstPoint,2,8,4,ThstIndexable>;
    return thst_query(data, points.empty() ? nullptr :
        std::make_shared<Tree>(points.begin(),points.end()));
}
#endif
