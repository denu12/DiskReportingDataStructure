#include "sfc/circle.hh"
// TODO: XXXX-3 needs credit where credit due
#pragma once

#include <algorithm>
#include <cmath>
#include <execution>
#include <map>
#include <tuple>
#include <vector>

#include "absl/container/btree_map.h"
#include "immintrin.h"
namespace diskreport::sfc::dynamic {

#ifdef PARALLEL
constexpr auto policy = std::execution::par;
#else
constexpr auto policy = std::execution::seq;
#endif

template <typename>
struct rank_t;
template <>
struct rank_t<u_int8_t> {
  using type = u_int16_t;
};
template <>
struct rank_t<u_int16_t> {
  using type = u_int32_t;
};
template <>
struct rank_t<u_int32_t> {
  using type = u_int64_t;
};

template <typename T>
struct Point1 {
  using ElementType = T;
  T x;
  T y;

  bool operator<(const Point1& o) const { return x < o.x; }
};

template <template <typename, typename> typename TreeType, typename Input_t,
          typename Key_t = Input_t, bool hilbert = true>
struct HCDS {
  using Rank_t = typename rank_t<Key_t>::type;
  using PointType = Point1<Input_t>;
  using Point = PointType;
  using IDXT = Input_t;
  struct Query {
    using PT = Point;
    using PointType = PT;
    PT p, q;
    // double d;
    Query(PointType p, PointType q) : p(p), q(q) {}
    Query(typename PointType::ElementType x, typename PointType::ElementType y,
          typename PointType::ElementType u, typename PointType::ElementType v)
        : p(x, y), q(u, v){};
  };
  using QueryType = Query;
  static inline u_int64_t interleave(u_int64_t x, u_int64_t mask) { return _pdep_u64(x, mask); }

  constexpr static auto max_number_of_bits = sizeof(Key_t) * 8;
  constexpr static Input_t W = std::numeric_limits<Key_t>::max();
  constexpr static Input_t H = std::numeric_limits<Key_t>::max();
  Input_t x_l = 0, y_l = 0, x_u = std::numeric_limits<Input_t>::max(),
          y_u = std::numeric_limits<Input_t>::max(), S = 1;

  TreeType<Rank_t, PointType> tree;

  HCDS() = default;

  // Construct by associative sorting
  explicit HCDS(const std::vector<Point>& input) {
    std::vector<std::pair<Rank_t, Point>> temp;
    temp.reserve(input.size());

    // Zip
    for (const Point& p : input) {
      temp.emplace_back(std::make_pair(getRank(p.x, p.y), p));
    }

    // Sort
    std::sort(policy, temp.begin(), temp.end(),
              [](const std::pair<Rank_t, Point>& lhs, const std::pair<Rank_t, Point>& rhs) {
                return lhs.first < rhs.first;
              });

    // Unzip
    tree = TreeType<Rank_t, PointType>(temp.cbegin(), temp.cend());
  }

  // Compute the rank of a point (x,y) in the quadtree
  static Rank_t getRankQuadtree(const Key_t x, const Key_t y,
                                const size_t& max_depth = max_number_of_bits) {
    // Mask for all odd bits (101010... in binary)
    const uint64_t odd_mask = 0xAAAAAAAAAAAAAAAAULL;
    // Mask for all even bits (010101... in binary)
    const uint64_t even_mask = 0x5555555555555555ULL;

    // Deposit bits of 'y' into the even positions
    uint64_t y_interleaved = interleave((uint64_t)y >> (max_number_of_bits - max_depth), odd_mask);

    // Deposit bits of 'x' into the odd positions
    uint64_t x_interleaved = interleave((uint64_t)x >> (max_number_of_bits - max_depth), even_mask);

    // Combine the results
    Rank_t result2 =
        (x_interleaved | y_interleaved)
        << (2 * (max_number_of_bits - max_depth));  //<< (2 * (max_number_of_bits - max_depth));
    return result2;
  }

  static Rank_t getRankHilbertViaLookup(const Key_t x, const Key_t y,
                                        const size_t max_depth = max_number_of_bits) {
    // int rotation = 1;
    static constexpr std::array<unsigned char, 16> lut = {4,  15, 1, 2,  0,  5, 11, 6,
                                                          10, 9,  7, 12, 14, 3, 13, 8};
    int shift = (max_number_of_bits - 1);

    Key_t ydigit = (y >> (shift)) & 1;
    Key_t xdigit = (x >> (--shift)) & 2;

    Rank_t result = lut[1 << 2 | (xdigit) | (ydigit)] & 3;
    int rotation = (lut[1 << 2 | (xdigit) | (ydigit)] & 12);
    for (size_t depth = 2; depth <= max_depth; ++depth) {
      Key_t ydigit = (y >> shift) & 1;
      Key_t xdigit = ((x >> shift) & 1) << 1;
      --shift;  // shift one less and take the second least significant bit --> saves one operation

      result = result << 2;

      int suffix = lut[rotation | (xdigit) | (ydigit)] & 3;
      // We consider rotation 1
      // Π = 00, 01, 10, 11
      // We do rotation 2
      // ⊂ = 10, 01, 00, 11

      // Based on the current rotation, and the suffix we just added,
      // we get a new rotation number

      rotation = (lut[rotation | (xdigit) | (ydigit)] & 12);
      result += suffix;
    }

    result = result << (2 * (max_number_of_bits - max_depth));
    return result;
  }

  static Rank_t getRank(const Key_t x, const Key_t y, const size_t max_depth = max_number_of_bits) {
    if constexpr (hilbert)
      return getRankHilbertViaLookup(x, y, max_depth);
    else
      return getRankQuadtree(x, y, max_depth);
  }

  // Input: a single corner (x, y) of a query square with diameter [diameter]
  // Output: the lower bound and upper bound of ranks corresponding to this
  // corner.
  static std::pair<Rank_t, Rank_t> getQueryMinAndMax(const Key_t& x, const Key_t& y,
                                                     const size_t max_depth) {
    // consider the maximum integer s = 2^x such that s < radius
    // the integer max_depth = x
    //  The lower bound is the coordinate of x, y if we were to stop computing
    //  after max_depth
    // Closed rank interval: no overflowing one-past-the-end sentinel.
    const size_t suffix_bits = 2 * (max_number_of_bits - max_depth);
    if (suffix_bits == sizeof(Rank_t) * 8) {
      return {0, std::numeric_limits<Rank_t>::max()};
    }
    const Rank_t first = getRank(x, y, max_depth);
    const Rank_t mask = (Rank_t(1) << suffix_bits) - 1;
    return {first, Rank_t(first | mask)};
  }
  std::array<std::pair<Rank_t, Rank_t>, 4> report_ranges;
  template <typename T>
  static inline void sort4(std::array<T, 4>& array) {
    if (array[0].first > array[1].first) std::swap(array[0], array[1]);
    if (array[2].first > array[3].first) std::swap(array[2], array[3]);
    if (array[0].first > array[2].first) std::swap(array[0], array[2]);
    if (array[1].first > array[3].first) std::swap(array[1], array[3]);
    if (array[1].first > array[2].first) std::swap(array[1], array[2]);
  }
  void query(const PointType& p, const PointType& q, auto&& output) {
    if (p.x > q.x || p.y > q.y) return;
    const Key_t diameter = std::max(q.x - p.x, q.y - p.y);
    // We generate a report range for each corner of the rectangle
    const size_t max_depth = (diameter == 0 ? max_number_of_bits : __builtin_clz(diameter) - (32 - max_number_of_bits));
    report_ranges[0] = (getQueryMinAndMax(p.x, p.y, max_depth));
    report_ranges[1] = (getQueryMinAndMax(q.x, p.y, max_depth));
    report_ranges[2] = (getQueryMinAndMax(p.x, q.y, max_depth));
    report_ranges[3] = (getQueryMinAndMax(q.x, q.y, max_depth));

    // std::sort(report_ranges.begin(), report_ranges.end());
    sort4(report_ranges);
    PointType val;
    Rank_t lowerbound, upperbound;
    auto start = tree.begin();
    auto end = tree.end();
    for (const auto& report_range : report_ranges) {
      lowerbound = report_range.first;
      upperbound = report_range.second;
      if (start != tree.end() && start->first < lowerbound) {
        auto start2 = tree.lower_bound(lowerbound);
        if (start2 == tree.end()) {
          break;
        }
        start = start2;
      }
      if (start != tree.end() && start->first <= upperbound) {
        end = tree.upper_bound(upperbound);
      } else {
        end = start;
      }
      while (start != end) {
        val = start->second;
        // TODO  replace this with q
        if (::esa_campaign::point_membership(val, p, q)) {
          *output = val;
        }
        start++;
      }

      start = end;
      if (end == tree.end()) {
        break;
      }
      end = tree.end();  // This can be optimised?
    }
  }
  void query(const QueryType& q, auto&& out) { query(q.p, q.q, out); }
  void insert(const Point p) { tree.insert({getRank(p.x, p.y), p}); }

  void remove(const Point p) {
    auto rn = getRank(p.x, p.y);
    auto it = tree.find(rn);
    tree.erase(it);
  }
};
}  // namespace diskreport::sfc::dynamic
