// Morton: scalar 2D baseline, without an early-termination oracle.
// Built with compiler auto-vectorization disabled (see BUILD).
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <immintrin.h>
#include <limits>
#include <type_traits>
#include <vector>
#include "app/algorithms/sfc/sfc.hh"
namespace diskreport::morton_Morton {

// The circle comes from the benchmark query context. Test membership here,
// while visiting the point, and output the actual coordinates individually.
template <class P>
bool contains(P p, P lo, P hi) {
  const auto* circle = ::esa_campaign::active_circle;
  if (!circle) return p.x >= lo.x && p.x <= hi.x && p.y >= lo.y && p.y <= hi.y;
  const uint64_t dx = p.x > circle->x ? uint64_t(p.x) - circle->x : uint64_t(circle->x) - p.x;
  const uint64_t dy = p.y > circle->y ? uint64_t(p.y) - circle->y : uint64_t(circle->y) - p.y;
  using Wide = unsigned __int128;
  const Wide radius2 = (Wide(circle->radius2_hi) << 64) | circle->radius2_lo;
  return Wide(dx) * dx + Wide(dy) * dy <= radius2;
}

class Morton {
 public:
  using IDXT = uint32_t;
  using PointType = ::diskreport::sfc::Point<uint32_t>;
  using QueryType = ::diskreport::sfc::Query<PointType>;
  using Rank = uint64_t;
  static constexpr bool reports_exact_circle = true;

  explicit Morton(const std::vector<PointType>& input) : ranks(input.size()) {
    // Original associative sort: zip ranks with points, sort, then unzip.
    std::vector<std::pair<Rank, PointType>> sorted;
    sorted.reserve(input.size());
    for (const auto p : input) sorted.emplace_back(morton(p.x, p.y), p);
    std::sort(sorted.begin(), sorted.end(),
              [](const auto& a, const auto& b) { return a.first < b.first; });
    points.reserve(sorted.size());
    for (size_t i = 0; i < sorted.size(); ++i) {
      ranks[i] = sorted[i].first;
      points.push_back(sorted[i].second);
    }

  }

  void query(const QueryType& q, auto&& output) const {
    const auto lo = q.p, hi = q.q;
    if (lo.x > hi.x || lo.y > hi.y) return;

    // The bounding square meets at most four cells at this quadtree depth.
    const uint32_t diameter = std::max(hi.x - lo.x, hi.y - lo.y);
    const unsigned depth = diameter == 0 ? 32 : __builtin_clz(diameter);
    std::array<std::pair<Rank, Rank>, 4> ranges = {
        interval(lo.x, lo.y, depth), interval(hi.x, lo.y, depth),
        interval(lo.x, hi.y, depth), interval(hi.x, hi.y, depth)};
    sort4(ranges);
    size_t start = 0;
    for (const auto [first, last] : ranges) {
      if (start < points.size() && ranks[start] < first) start = lower_bound(first);
      const size_t end = start < points.size() && ranks[start] <= last
                             ? upper_bound(last) : start;
      for (size_t i = start; i < end; ++i) {
        if (contains(points[i], lo, hi)) *output++ = points[i];
      }
      // Sorted intervals may repeat; never report a point twice.
      start = end;
    }
  }

 private:
  std::vector<PointType> points;
  std::vector<Rank> ranks;

  // Original Morton encoding. PDEP deposits scalar bits; it is not SIMD.
  static Rank morton(uint32_t x, uint32_t y) {
    return _pdep_u64(x, UINT64_C(0x5555555555555555)) |
           _pdep_u64(y, UINT64_C(0xaaaaaaaaaaaaaaaa));
  }
  static std::pair<Rank, Rank> interval(uint32_t x, uint32_t y, unsigned depth) {
    const unsigned suffix_bits = 2 * (32 - depth);
    if (suffix_bits == 64) return {0, UINT64_MAX};
    const Rank suffix_mask = (Rank(1) << suffix_bits) - 1;
    const Rank first = morton(x, y) & ~suffix_mask;
    return {first, first | suffix_mask};
  }
  static void sort4(std::array<std::pair<Rank, Rank>, 4>& a) {
    // Original five-comparison sorting network.
    if (a[0].first > a[1].first) std::swap(a[0], a[1]);
    if (a[2].first > a[3].first) std::swap(a[2], a[3]);
    if (a[0].first > a[2].first) std::swap(a[0], a[2]);
    if (a[1].first > a[3].first) std::swap(a[1], a[3]);
    if (a[1].first > a[2].first) std::swap(a[1], a[2]);
  }
  // Scalar binary search on the Morton-sorted ranks.
  size_t lower_bound(Rank key) const {
    return std::lower_bound(ranks.begin(), ranks.end(), key) - ranks.begin();
  }
  size_t upper_bound(Rank key) const {
    return std::upper_bound(ranks.begin(), ranks.end(), key) - ranks.begin();
  }

};

using Adapter = ::diskreport::sfc::app::algorithms::sfc::Algo<Morton>;
REGISTER_IMPL_NAMED(Adapter, "Morton");
}  // namespace diskreport::morton_Morton
