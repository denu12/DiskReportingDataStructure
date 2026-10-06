// TODO: XXXX-3 needs credit where credit due

#include <sys/types.h>

#include <algorithm>
#include <array>
#include <bitset>
#include <cmath>
#include <execution>
#include <limits>
#include <tuple>
#include <vector>

#include "hwy/highway.h"
#include "sfc/common.hh"
HWY_BEFORE_NAMESPACE();

namespace diskreport::sfc {
namespace HWY_NAMESPACE {

template <template <typename> typename LB, typename Input_t, typename Key_t = Input_t,
          int EarlyMaxDepth = 26, bool hilbert = true, bool layered = true,
          int powerCovered = EarlyMaxDepth>
struct EHCDS {
  using Rank_t = typename rank_t<Key_t>::type;
  using PointType = Point<Input_t>;
  using QueryType = Query<PointType>;
  using IDXT = Input_t;
  constexpr static int max_number_of_bits = sizeof(Key_t) * 8;
  constexpr static auto shift_for_early = 2 * max_number_of_bits - EarlyMaxDepth;
  std::vector<PointType> points;
  LB<Rank_t> ranks;
  std::vector<bool> early_oracle2;
  std::vector<bool> early_oracle;

  // Construct by associative sorting
  explicit EHCDS(const std::vector<PointType>& input)
      : ranks(input.size()), early_oracle(1 << EarlyMaxDepth, false) {
    if constexpr (layered) {
      // for (int i = 0; i < powerCovered; i++) {
      //   early_oracle2[i].resize(1 << (EarlyMaxDepth - i), false);
      // }
      // early_oracle2[powerCovered].resize(1, true);
      early_oracle2.resize((1 << (EarlyMaxDepth + 1)) - (1 << (EarlyMaxDepth - powerCovered)) - 1,
                           false);
      early_oracle2.back() = true;
    }
    points.resize(input.size());
    // ranks.resize(input.size());
    std::vector<std::pair<Rank_t, PointType>> temp;
    temp.resize(input.size());

    // Zip
    std::transform(input.begin(), input.end(), temp.begin(),
                   [](auto& p) -> std::pair<Rank_t, PointType> {
                     return std::make_pair(getRank(p.x, p.y), p);
                   });
    // Sort
    std::sort(policy, temp.begin(), temp.end(),
              [](const std::pair<Rank_t, PointType>& lhs, const std::pair<Rank_t, PointType>& rhs) {
                return lhs.first < rhs.first;
              });
    // Unzip
    std::transform(temp.begin(), temp.end(), ranks.btree.get(), [](auto& p) { return p.first; });

    if constexpr (layered) {
      if (temp.size() * powerCovered < (1 << EarlyMaxDepth)) {
        for (const auto& p : temp) {
          auto res = getRankQuadtree(p.second.x, p.second.y) >> shift_for_early;
          for (int i = 0; i < powerCovered; i++) {
            early_oracle2[all - elementsInEbenen(i) + res] = 1;
            res >>= 1;
          }
        }
      } else {
        for (const auto& p : temp) {  // init first
          early_oracle2[getRankQuadtree(p.second.x, p.second.y) >> (shift_for_early)] = 1;
        }
        // propagate info
        size_t current = 0;
        for (int i = 0; i < powerCovered - 1; i++) {
          size_t offset = current + (1 << (powerCovered - i));
          for (size_t e = 0; e < (1 << (powerCovered - i - 1)); e++) {
            early_oracle2[offset + e] = early_oracle2[current] | early_oracle2[current + 1];
            current += 2;
          }
        }
      }
    } else {
      for (const auto& p : temp) {  // init first
        early_oracle[getRankQuadtree(p.second.x, p.second.y) >> (shift_for_early)] = 1;
      }
    }
    ranks.build();
    std::transform(temp.begin(), temp.end(), points.begin(), [](auto& p) { return p.second; });
  }

  // Compute the rank of a point (x,y) in the quadtree
  static Rank_t getRankQuadtree(const Key_t x, const Key_t y,
                                const size_t& max_depth = max_number_of_bits) {
    // Mask for all odd bits (101010... in binary)
    const uint64_t odd_mask = 0xAAAAAAAAAAAAAAAAULL;
    // Mask for all even bits (010101... in binary)
    const uint64_t even_mask = 0x5555555555555555ULL;

    // Deposit bits of 'y' into the even positions
    uint64_t y_interleaved =
        rank_t<Key_t>::interleave(y >> (max_number_of_bits - max_depth), odd_mask);

    // Deposit bits of 'x' into the odd positions
    uint64_t x_interleaved =
        rank_t<Key_t>::interleave(x >> (max_number_of_bits - max_depth), even_mask);

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
  static std::pair<Rank_t, Rank_t> getQueryMinAndMax(const Key_t x, const Key_t y,
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
  void query(const QueryType& q, auto&& output) {
    // std::cout << q.p.x << " " << q.p.y << std::endl;
    query(q.p, q.q, output);
  }
  std::array<std::pair<Rank_t, Rank_t>, 4> report_ranges;
  static constexpr int elementsInEbenen(int i) { return (1 << (EarlyMaxDepth + 1 - i)) - 1; }
  static constexpr int all = elementsInEbenen(EarlyMaxDepth - powerCovered);
  template <typename T>
  static inline void sort4(std::array<T, 4>& array) {
    if (array[0].first > array[1].first) std::swap(array[0], array[1]);
    if (array[2].first > array[3].first) std::swap(array[2], array[3]);
    if (array[0].first > array[2].first) std::swap(array[0], array[2]);
    if (array[1].first > array[3].first) std::swap(array[1], array[3]);
    if (array[1].first > array[2].first) std::swap(array[1], array[2]);
  }
  inline bool early_exit(Rank_t p, const Rank_t q) {
    if constexpr (layered) {
      Rank_t common_zeros = ((p ^ q) >> (shift_for_early - 1)) |
                            1;  // 1 where the first is, so no undefined behaviour
      const int i =
          std::min(2 * max_number_of_bits - __builtin_clzll(common_zeros) - 1, powerCovered);
      const bool valid = i != powerCovered;  // p is 0 if i>powerCovered
      p >>= i + shift_for_early;             //
      // std::cout << p << " " << i << std::endl;
      const int this_layer_offset = all - elementsInEbenen(i);
      p = p * valid + this_layer_offset;
      // std::cout << p << " " << overall << std::endl;
      return valid && !early_oracle2[p];
    }
    auto r_p = p >> shift_for_early;
    auto r_q = q >> shift_for_early;
    return r_p == r_q && !early_oracle[r_p];
  }
  inline bool early_exit(const PointType p, const PointType q) {
    return early_exit(getRankQuadtree(p.x, p.y), getRankQuadtree(q.x, q.y));
  }
  void query(const PointType p, const PointType q, auto&& output) {
    if (p.x > q.x || p.y > q.y) return;
    if (early_exit(p, q)) {
      // std::cout << "Early terminate" << std::endl;
      return;
    }
    const Key_t diameter = std::max(q.x - p.x, q.y - p.y);
    const size_t max_depth =
        (diameter == 0 ? max_number_of_bits : __builtin_clz(diameter) - (32 - max_number_of_bits));  // works only upto 32 bits
    report_ranges[0] = getQueryMinAndMax(p.x, p.y, max_depth);
    report_ranges[1] = getQueryMinAndMax(q.x, p.y, max_depth);
    report_ranges[2] = getQueryMinAndMax(p.x, q.y, max_depth);
    report_ranges[3] = getQueryMinAndMax(q.x, q.y, max_depth);
    // std::sort(report_ranges.begin(), report_ranges.end());
    // auto max_r = std::max(std::max(report_ranges[0].second, report_ranges[1].second),
    //                       std::max(report_ranges[2].second, report_ranges[3].second));
    sort4(report_ranges);

    PointType val;

    size_t start = 0;
    size_t end = points.size();
    for (const auto report_range : report_ranges) {
      if (start < points.size() && ranks[start] < report_range.first) {
        start = ranks.lower_bound(report_range.first);  // std::lower_bound(start, end, lowerbound);
      }
      if (start < points.size() && ranks[start] <= report_range.second) {
        end = ranks.upper_bound(report_range.second);  // std::upper_bound(start, end, upperbound);
      } else {
        end = start;
      }
      for (; start < end; start++) {
        val = points[start];
        // TODO  replace this with q
        if (::esa_campaign::point_membership(val, p, q)) {
          *output = val;
        }
      }

      start = end;
      if (start == points.size()) {
        break;
      }
      end = points.size();  // This can be optimised?
    }
  }
};
}  // namespace HWY_NAMESPACE
}  // namespace diskreport::sfc