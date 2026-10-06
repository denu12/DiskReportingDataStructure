#pragma once
#include <algorithm>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <random>
#include <vector>
#include "sfc/common.hh"

namespace diskreport::sfc::app::algorithms::sfc {
// Exact 2D box-reporting adaptation of Timothy Chan's static SSS (2005/2006).
// See third_party/chan_sss/NOTICE.txt and the unmodified upstream source.
// This is not Chan's original approximate-nearest-neighbor query algorithm.
class ChanSSS {
 public:
  using IDXT = uint32_t;
  using PointType = Point<IDXT>;
  using QueryType = Query<PointType>;

  explicit ChanSSS(const std::vector<PointType>& points, uint64_t seed = 12121)
      : index_(points), shift_(static_cast<uint32_t>(std::mt19937_64(seed)())) {
    std::sort(index_.begin(), index_.end(), [this](const auto& a, const auto& b) {
      return less(shifted(a), shifted(b));
    });
  }

  template <class Output> void query(const QueryType& q, Output out) const {
    if (q.p.x > q.q.x || q.p.y > q.q.y) return;
    search(0, index_.size(), shifted(q.p), shifted(q.q), out);
  }

 private:
  // A 32-bit shift plus a full uint32 coordinate needs 33 bits. Do not wrap.
  struct WidePoint { uint64_t x, y; };
  std::vector<PointType> index_;
  uint64_t shift_;
  WidePoint shifted(PointType p) const { return {p.x + shift_, p.y + shift_}; }

  // Chan's less_msb comparator; x wins ties between coordinate bit positions.
  static bool less(WidePoint a, WidePoint b) {
    const uint64_t x = a.x ^ b.x, y = a.y ^ b.y;
    return (x < y && x < (x ^ y)) ? a.y < b.y : a.x < b.x;
  }

  template <class Output>
  void search(size_t first, size_t last, WidePoint lo, WidePoint hi, Output& out) const {
    if (first == last) return;
    const auto a = shifted(index_[first]), b = shifted(index_[last - 1]);
    // A Morton-sorted subarray lies inside the common quadtree cell of its
    // endpoints. Replace Chan's distance-to-cell test by exact disjointness.
    const unsigned bits = std::bit_width((a.x ^ b.x) | (a.y ^ b.y));
    const uint64_t mask = (uint64_t{1} << bits) - 1; // bits <= 33
    const uint64_t x = a.x & ~mask, y = a.y & ~mask;
    if (hi.x < x || hi.y < y || lo.x > (x | mask) || lo.y > (y | mask)) return;
    const size_t mid = first + (last - first) / 2;
    const auto p = shifted(index_[mid]);
    if (p.x >= lo.x && p.x <= hi.x && p.y >= lo.y && p.y <= hi.y)
      *out++ = index_[mid];
    // The lower/upper rectangle corners bound its Morton interval. Inclusive
    // comparisons preserve all duplicate points and points on the boundary.
    if (!less(p, lo)) search(first, mid, lo, hi, out);
    if (!less(hi, p)) search(mid + 1, last, lo, hi, out);
  }
};
}  // namespace diskreport::sfc::app::algorithms::sfc
