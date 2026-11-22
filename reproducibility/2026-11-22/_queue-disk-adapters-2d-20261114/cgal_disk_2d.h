#pragma once

#include <CGAL/Simple_cartesian.h>
#include <CGAL/Search_traits_2.h>
#include <CGAL/Kd_tree.h>

const char* output_contract = "floating_points";
const char* output_representation = "native_cgal_points";
const char* membership_contract = "closed_integer_ball";

using CgalKernel = CGAL::Simple_cartesian<double>;
using CgalTraits = CGAL::Search_traits_2<CgalKernel>;
using CgalPoint = CgalTraits::Point_d;

struct CgalDiskQuery {
    Disk2D disk;

    bool contains(const CgalPoint& point) const {
        return disk.contains(point.x(), point.y());
    }

    template<class Rectangle>
    bool inner_range_intersects(const Rectangle& rectangle) const {
        // All split coordinates are in the uint32 grid. Round toward the
        // center conservatively if a split coordinate is fractional.
        const auto x = std::clamp(double(disk.center[0]), rectangle.min_coord(0), rectangle.max_coord(0));
        const auto y = std::clamp(double(disk.center[1]), rectangle.min_coord(1), rectangle.max_coord(1));
        return disk.contains(x < disk.center[0] ? std::ceil(x) : std::floor(x),
                             y < disk.center[1] ? std::ceil(y) : std::floor(y));
    }

    template<class Rectangle>
    bool outer_range_contains(const Rectangle& rectangle) const {
        auto farthest = [&](unsigned a) {
            const double center = disk.center[a];
            const double lo = rectangle.min_coord(a), hi = rectangle.max_coord(a);
            return center - lo > hi - center ? std::floor(lo) : std::ceil(hi);
        };
        return disk.contains(farthest(0), farthest(1));
    }
};

inline Query create(Data& data, const std::string&) {
    using Tree = CGAL::Kd_tree<CgalTraits>;
    std::vector<CgalPoint> points;
    points.reserve(data.points.size());
    for (const auto& p : data.points) points.emplace_back(p[0], p[1]);
    auto tree = std::make_shared<Tree>(points.begin(), points.end());
    if (!points.empty()) tree->build();
    auto hits = std::make_shared<std::vector<CgalPoint>>();
    return {
        [&, tree, hits](std::size_t q) {
            hits->clear();
            if (!tree->empty()) tree->search(std::back_inserter(*hits),
                CgalDiskQuery{Disk2D(data.centers[q], data.radii[q])});
            asm volatile("" : : "r"(hits->data()), "r"(hits->size()) : "memory");
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
