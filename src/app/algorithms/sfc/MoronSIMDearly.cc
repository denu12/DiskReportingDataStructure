// MoronSIMDearly: original SIMD rank search, exact SIMD circle reporting and early termination.
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

#include "hwy/aligned_allocator.h"
#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "app/algorithms/sfc/MoronSIMDearly.cc"
#include "hwy/foreach_target.h"
#include "hwy/highway.h"
HWY_BEFORE_NAMESPACE();
namespace diskreport::morton_MoronSIMDearly::HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;

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
template <typename ValueType>
struct RankIndex {
  using DataType = ValueType;
  static constexpr const hn::ScalableTag<ValueType> d{};
#if HWY_HAVE_CONSTEXPR_LANES
  static const HWY_LANES_CONSTEXPR size_t B = 2 * hn::Lanes(d);
#else
  const size_t B;
#endif
  HWY_LANES_CONSTEXPR size_t blocks(size_t n) { return (n + B - 1) / B; }
  HWY_LANES_CONSTEXPR size_t prev_keys(size_t n) { return (blocks(n) + B) / (B + 1) * B; }
  HWY_LANES_CONSTEXPR size_t height(size_t n) { return (n <= B ? 1 : height(prev_keys(n)) + 1); }
  const size_t N;
  const size_t H;
  size_t overall_size;
  std::vector<size_t> offsets;
  hwy::AlignedFreeUniquePtr<ValueType[]> btree;
  explicit RankIndex(const size_t N)
      :
#if !HWY_HAVE_CONSTEXPR_LANES
        B(2 * hn::Lanes(d)),
#endif
        N(N),
        H(height(N))

  {
    offsets.resize(H + 1, 0);
    size_t k = 0, n = N;
    for (size_t i = 1; i < H; i++) {
      k += blocks(n) * B;  // every offset is multiple of B
      n = prev_keys(n);
      offsets[i] = k;
    }
    overall_size = k + B;
    offsets[H] = overall_size;
    btree = hwy::AllocateAligned<ValueType>(overall_size);
  }
  explicit RankIndex(const std::vector<ValueType>& values)
      : RankIndex(values.size()) {
    std::copy(values.begin(), values.end(), btree.get());
    build();
  }
  static const constexpr ValueType max_value = std::numeric_limits<ValueType>::max();
  ValueType operator[](size_t i) const { return btree[i]; }
  void build() {
    // pad the array
    std::fill(btree.get() + N, btree.get() + overall_size, max_value);
    // build layer by layer
    for (size_t h = 1; h < H; h++) {
      for (size_t i = 0; i < offsets[h + 1] - offsets[h]; i++) {
        // i = k * B + j
        size_t k = (i / B), j = i - (k * B);
        k = k * (B + 1) + j + 1;  // compare to the right of the key
        // and then always to the left
        for (size_t l = 0; l < h - 1; l++) k *= (B + 1);
        // pad the rest with infinities if the key doesn't exist
        btree[offsets[h] + i] = ((k * B) < N ? btree[k * B] : max_value);
      }
    }
  }
  HWY_INLINE size_t lower_bound(const ValueType _x) const {
    size_t k = 0;  // we assume k already multiplied by B to optimize pointer arithmetic
    auto x = hn::Set(d, _x);
    __restrict__ ValueType* btree_ = btree.get();
    for (size_t h = H - 1; h > 0; h--) {
      auto i = hn::CountTrue(d, hn::Lt(hn::Load(d, btree_ + offsets[h] + k), x)) +
               hn::CountTrue(d, hn::Lt(hn::Load(d, btree_ + offsets[h] + k + B / 2), x));
      k = k * (B + 1) + (i * B);
    }
    auto i = hn::CountTrue(d, hn::Lt(hn::Load(d, btree_ + k), x)) +
             hn::CountTrue(d, hn::Lt(hn::Load(d, btree_ + k + B / 2), x));

    auto result = (k + i);
    return result;
  }
  HWY_INLINE size_t upper_bound(const ValueType _x) const {
    if (N == 0 || _x >= *(btree.get() + N - 1)) return N;
    size_t k = 0;  // we assume k already multiplied by B to optimize pointer arithmetic
    auto x = hn::Set(d, _x);
    __restrict__ ValueType* btree_ = btree.get();
    for (size_t h = H - 1; h > 0; h--) {
      auto i = hn::CountTrue(d, hn::Le(hn::Load(d, btree_ + offsets[h] + k), x)) +
               hn::CountTrue(d, hn::Le(hn::Load(d, btree_ + offsets[h] + k + B / 2), x));
      k = k * (B + 1) + (i * B);
    }
    auto i = hn::CountTrue(d, hn::Le(hn::Load(d, btree_ + k), x)) +
             hn::CountTrue(d, hn::Le(hn::Load(d, btree_ + k + B / 2), x));

    auto result = (k + i);
    return result;
  }
};
// Full-range uint32 coordinates: each squared difference fits in uint64,
// but their sum needs 65 bits. Compare (carry, sum) with the uint128 radius.
// Packing moves actual point coordinates, preserving their scan order.
template <typename P, typename Output>
HWY_INLINE void report_circle_simd(const P* points, size_t start, size_t end,
                                  P lo, P hi, Output& output) {
  static_assert(std::is_same_v<typename P::ElementType, uint32_t>);
  static_assert(sizeof(P) == 8 && offsetof(P, y) == 4);
  const auto* circle = ::esa_campaign::active_circle;
#if HWY_TARGET != HWY_SCALAR && HWY_ARCH_X86
  if (circle) {
    namespace hn = hwy::HWY_NAMESPACE;
    const hn::ScalableTag<uint64_t> d;
    const hn::Repartition<uint8_t, decltype(d)> bytes;
    const hn::Repartition<uint32_t, decltype(d)> halves;
    const size_t lanes = hn::Lanes(d);
    const auto mask32 = hn::Set(d, UINT64_C(0xffffffff));
    const auto cx = hn::Set(d, uint64_t(circle->x));
    const auto cy = hn::Set(d, uint64_t(circle->y));
    const auto radius_lo = hn::Set(d, circle->radius2_lo);
    const auto radius_hi = hn::Set(d, circle->radius2_hi);
    HWY_ALIGN uint64_t packed[hn::MaxLanes(d)];
    for (; end - start >= lanes; start += lanes) {
      // Byte loads avoid aliasing a Point array as uint64_t objects. On x86,
      // each little-endian lane contains x in its low half and y in its high half.
      const auto xy = hn::BitCast(d, hn::LoadU(bytes,
          reinterpret_cast<const uint8_t*>(points + start)));
      const auto x = hn::And(xy, mask32);
      const auto y = hn::ShiftRight<32>(xy);
      const auto dx = hn::Sub(hn::Max(x, cx), hn::Min(x, cx));
      const auto dy = hn::Sub(hn::Max(y, cy), hn::Min(y, cy));
      // High halves of dx/dy are zero; widen the low uint32 products.
      const auto dx32 = hn::BitCast(halves, dx);
      const auto dy32 = hn::BitCast(halves, dy);
      const auto xx = hn::MulEven(dx32, dx32);
      const auto yy = hn::MulEven(dy32, dy32);
      const auto sum = hn::Add(xx, yy);
      const auto carry = hn::IfThenElse(hn::Lt(sum, xx), hn::Set(d, 1), hn::Zero(d));
      const auto inside = hn::Or(hn::Lt(carry, radius_hi),
          hn::And(hn::Eq(carry, radius_hi), hn::Not(hn::Gt(sum, radius_lo))));
      const size_t count = hn::CompressStore(xy, inside, d, packed);
      for (size_t i = 0; i < count; ++i) {
        P point;
        std::memcpy(&point, &packed[i], sizeof(point));
        *output++ = point;
      }
    }
  }
#endif
  // Scalar tail, non-circle queries, and targets without this SIMD kernel.
  for (; start < end; ++start) {
    const auto p = points[start];
    if (contains(p, lo, hi)) *output++ = p;
  }
}

class MoronSIMDearly {
 public:
  using IDXT = uint32_t;
  using PointType = ::diskreport::sfc::Point<uint32_t>;
  using QueryType = ::diskreport::sfc::Query<PointType>;
  using Rank = uint64_t;
  static constexpr bool reports_exact_circle = true;

  explicit MoronSIMDearly(const std::vector<PointType>& input) : ranks(input.size()) {
    // Original associative sort: zip ranks with points, sort, then unzip.
    std::vector<std::pair<Rank, PointType>> sorted;
    sorted.reserve(input.size());
    for (const auto p : input) sorted.emplace_back(morton(p.x, p.y), p);
    std::sort(sorted.begin(), sorted.end(),
              [](const auto& a, const auto& b) { return a.first < b.first; });
    points.reserve(sorted.size());
    for (size_t i = 0; i < sorted.size(); ++i) {
      ranks.btree[i] = sorted[i].first;
      points.push_back(sorted[i].second);
    }
    ranks.build();
    build_oracle();
  }

  void query(const QueryType& q, auto&& output) const {
    const auto lo = q.p, hi = q.q;
    if (lo.x > hi.x || lo.y > hi.y) return;
    if (early_exit(lo, hi)) return;
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
      report_circle_simd(points.data(), start, end, lo, hi, output);
      // Sorted intervals may repeat; never report a point twice.
      start = end;
    }
  }

 private:
  std::vector<PointType> points;
  RankIndex<Rank> ranks;

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
  size_t lower_bound(Rank key) const { return ranks.lower_bound(key); }
  size_t upper_bound(Rank key) const { return ranks.upper_bound(key); }

  // Original 24-level layered occupancy oracle from EHCDS.
  // Each layer is the OR of adjacent entries in the preceding layer.
  static constexpr int oracle_depth = 24;
  static constexpr int oracle_shift = 64 - oracle_depth;
  std::vector<bool> occupied;
  static constexpr size_t layer_size_sum(int level) {
    return (size_t(1) << (oracle_depth + 1 - level)) - 1;
  }
  void build_oracle() {
    occupied.resize((size_t(1) << (oracle_depth + 1)) - 2, false);
    occupied.back() = true;
    if (points.size() * oracle_depth < (size_t(1) << oracle_depth)) {
      for (const auto p : points) {
        Rank prefix = morton(p.x, p.y) >> oracle_shift;
        for (int level = 0; level < oracle_depth; ++level) {
          occupied[layer_size_sum(0) - layer_size_sum(level) + prefix] = true;
          prefix >>= 1;
        }
      }
    } else {
      for (const auto p : points) occupied[morton(p.x, p.y) >> oracle_shift] = true;
      size_t current = 0;
      for (int level = 0; level < oracle_depth - 1; ++level) {
        const size_t offset = current + (size_t(1) << (oracle_depth - level));
        for (size_t i = 0; i < (size_t(1) << (oracle_depth - level - 1)); ++i) {
          occupied[offset + i] = occupied[current] || occupied[current + 1];
          current += 2;
        }
      }
    }
  }
  bool early_exit(PointType lo, PointType hi) const {
    Rank first = morton(lo.x, lo.y);
    const Rank differing = ((first ^ morton(hi.x, hi.y)) >> (oracle_shift - 1)) | 1;
    const int level = std::min(63 - __builtin_clzll(differing), oracle_depth);
    if (level == oracle_depth) return false;
    first >>= level + oracle_shift;
    return !occupied[layer_size_sum(0) - layer_size_sum(level) + first];
  }

};

bool Register() {
  using Adapter = ::diskreport::sfc::app::algorithms::sfc::Algo<MoronSIMDearly>;
  return ::diskreport::app::algorithms::registerImpl<Adapter>("MoronSIMDearly");
}
}  // namespace diskreport::morton_MoronSIMDearly::HWY_NAMESPACE
HWY_AFTER_NAMESPACE();
#if HWY_ONCE
namespace diskreport::morton_MoronSIMDearly {
HWY_EXPORT(Register);
static const bool registered = [] { return HWY_DYNAMIC_DISPATCH(Register)(); }();
}
#endif
