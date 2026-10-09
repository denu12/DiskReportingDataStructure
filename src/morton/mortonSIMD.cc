// Standalone 2D MortonSIMD: C++20, x86-64 AVX2 and BMI2; no library dependencies.
// Include this file in a client compiled with -O3 -mavx2 -mbmi2.
#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <immintrin.h>
#include <utility>
#include <vector>
#if !defined(__AVX2__) || !defined(__BMI2__)
#error "Compile mortonSIMD.cc with -mavx2 -mbmi2"
#endif
namespace diskreport::morton_MortonSIMD {
using Wide = unsigned __int128;
struct Point {
  using ElementType = uint32_t;
  uint32_t x, y;
};
struct Box {
  Point p, q;
  Box(Point lo, Point hi) : p(lo), q(hi) {}
  Box(uint32_t x, uint32_t y, uint32_t u, uint32_t v) : p{x, y}, q{u, v} {}
};
struct Circle {
  Point center;
  Wide radius_squared;
  bool contains(Point p) const {
    const uint64_t dx = p.x > center.x ? uint64_t(p.x) - center.x : uint64_t(center.x) - p.x;
    const uint64_t dy = p.y > center.y ? uint64_t(p.y) - center.y : uint64_t(center.y) - p.y;
    return Wide(dx) * dx + Wide(dy) * dy <= radius_squared;
  }
  Box bounds() const {
    if (radius_squared >= Wide(2) * UINT32_MAX * UINT32_MAX)
      return {{0, 0}, {UINT32_MAX, UINT32_MAX}};
    uint64_t radius = uint64_t(std::ceil(std::sqrt(static_cast<long double>(radius_squared))));
    // Correct any floating-point rounding before forming the integer enclosure.
    while (Wide(radius) * radius < radius_squared) ++radius;
    while (radius && Wide(radius - 1) * (radius - 1) >= radius_squared) --radius;
    radius = std::min<uint64_t>(radius, UINT32_MAX);
    const Point lo{uint32_t(center.x > radius ? center.x - radius : 0),
                   uint32_t(center.y > radius ? center.y - radius : 0)};
    const Point hi{uint32_t(std::min<uint64_t>(UINT32_MAX, uint64_t(center.x) + radius)),
                   uint32_t(std::min<uint64_t>(UINT32_MAX, uint64_t(center.y) + radius))};
    return {lo, hi};
  }
};

// Unsigned 64-bit comparisons on AVX2: flip the sign bit before comparing.
inline __m256i less_unsigned(__m256i a, __m256i b) {
  const auto sign = _mm256_set1_epi64x(INT64_MIN);
  return _mm256_cmpgt_epi64(_mm256_xor_si256(b, sign), _mm256_xor_si256(a, sign));
}
struct RankIndex {
  // Original layered rank index, with two AVX2 vectors per node.
  static constexpr size_t B = 8;
  size_t N, H, overall_size;
  std::vector<size_t> offsets;
  std::vector<uint64_t> btree;
  static size_t blocks(size_t n) { return (n + B - 1) / B; }
  static size_t prev_keys(size_t n) { return (blocks(n) + B) / (B + 1) * B; }
  static size_t height(size_t n) { return n <= B ? 1 : height(prev_keys(n)) + 1; }
  explicit RankIndex(size_t n) : N(n), H(height(n)), offsets(H + 1) {
    size_t k = 0;
    for (size_t h = 1; h < H; ++h) { k += blocks(n) * B; n = prev_keys(n); offsets[h] = k; }
    overall_size = k + B; offsets[H] = overall_size; btree.resize(overall_size);
  }
  uint64_t operator[](size_t i) const { return btree[i]; }
  void build() {
    std::fill(btree.begin() + N, btree.end(), UINT64_MAX);
    for (size_t h = 1; h < H; ++h)
      for (size_t i = 0; i < offsets[h + 1] - offsets[h]; ++i) {
        size_t k = (i / B) * (B + 1) + i % B + 1;
        for (size_t l = 0; l < h - 1; ++l) k *= B + 1;
        btree[offsets[h] + i] = k * B < N ? btree[k * B] : UINT64_MAX;
      }
  }
  size_t lower_bound(uint64_t key) const {
    const auto x = _mm256_set1_epi64x(std::bit_cast<int64_t>(key));
    auto count = [&](size_t offset) {
      auto a = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(btree.data() + offset));
      auto b = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(btree.data() + offset + 4));
      unsigned mask = unsigned(_mm256_movemask_pd(_mm256_castsi256_pd(less_unsigned(a, x)))) |
          (unsigned(_mm256_movemask_pd(_mm256_castsi256_pd(less_unsigned(b, x)))) << 4);
      return size_t(std::popcount(mask));
    };
    size_t k = 0;
    for (size_t h = H - 1; h > 0; --h) k = k * (B + 1) + count(offsets[h] + k) * B;
    return k + count(k);
  }
  size_t upper_bound(uint64_t key) const {
    return N == 0 || key >= btree[N - 1] ? N : lower_bound(key + 1);
  }
};

class MortonSIMD {
 public:
  using IDXT = uint32_t;
  using PointType = Point;
  using QueryType = Box;
  using Rank = uint64_t;
  static constexpr bool reports_exact_circle = true;
  explicit MortonSIMD(const std::vector<PointType>& input) : ranks(input.size()) {
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

  }

  void query(Point center, uint64_t radius, auto output) const {
    query(Circle{center, Wide(radius) * radius}, output);
  }
  void query(const Circle& circle, auto output) const { scan(circle.bounds(), &circle, output); }
  void query(const Box& box, auto output) const { scan(box, nullptr, output); }
 protected:
  // Separate harness adapters can supply an already computed bounding square.
  void scan(const Box& box, const Circle* circle, auto output) const {
    const auto lo = box.p, hi = box.q;
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
      report(start, end, box, circle, output);
      // Sorted intervals may repeat; never report a point twice.
      start = end;
    }
  }
 private:
  std::vector<PointType> points;
  RankIndex ranks;

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


  void report(size_t start, size_t end, const Box& box, const Circle* circle, auto& output) const {
    if (circle) {
      static_assert(sizeof(Point) == 8 && offsetof(Point, y) == 4);
      const auto radius_lo = _mm256_set1_epi64x(std::bit_cast<int64_t>(uint64_t(circle->radius_squared)));
      const auto radius_hi = _mm256_set1_epi64x(std::bit_cast<int64_t>(uint64_t(circle->radius_squared >> 64)));
      // AVX2 compression table: preserve accepted points in scan order.
      static constexpr auto permutations = [] {
        std::array<std::array<int32_t, 8>, 16> table{};
        for (unsigned mask = 0; mask < 16; ++mask) {
          unsigned next = 0;
          for (unsigned lane = 0; lane < 4; ++lane) if (mask & (1u << lane)) {
            table[mask][next++] = 2 * lane; table[mask][next++] = 2 * lane + 1;
          }
        }
        return table;
      }();
      // Deinterleave eight contiguous points; widen even/odd squared distances.
      const auto cx32=_mm256_set1_epi32(circle->center.x),cy32=_mm256_set1_epi32(circle->center.y);
      for (; end - start >= 8; start += 8) {
        const auto a=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(points.data()+start));
        const auto b=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(points.data()+start+4));
        const auto x=_mm256_permute4x64_epi64(_mm256_castps_si256(_mm256_shuffle_ps(
            _mm256_castsi256_ps(a),_mm256_castsi256_ps(b),0x88)),0xd8);
        const auto y=_mm256_permute4x64_epi64(_mm256_castps_si256(_mm256_shuffle_ps(
            _mm256_castsi256_ps(a),_mm256_castsi256_ps(b),0xdd)),0xd8);
        const auto dx=_mm256_sub_epi32(_mm256_max_epu32(x,cx32),_mm256_min_epu32(x,cx32));
        const auto dy=_mm256_sub_epi32(_mm256_max_epu32(y,cy32),_mm256_min_epu32(y,cy32));
        unsigned mask=0;
        for(unsigned parity=0;parity<2;++parity) {
          const auto u=parity?_mm256_srli_epi64(dx,32):dx;
          const auto v=parity?_mm256_srli_epi64(dy,32):dy;
          const auto xx=_mm256_mul_epu32(u,u),yy=_mm256_mul_epu32(v,v);
          const auto sum=_mm256_add_epi64(xx,yy);
          const auto carry=_mm256_and_si256(less_unsigned(sum,xx),_mm256_set1_epi64x(1));
          const auto inside=_mm256_or_si256(less_unsigned(carry,radius_hi),
              _mm256_andnot_si256(less_unsigned(radius_lo,sum),_mm256_cmpeq_epi64(carry,radius_hi)));
          const unsigned bits=unsigned(_mm256_movemask_pd(_mm256_castsi256_pd(inside)));
          mask|=_pdep_u32(bits,parity?0xaa:0x55);
        }
        for(unsigned half=0;half<2;++half) {
          const unsigned selected=(mask>>(4*half))&15;
          if(!selected)continue;
          const auto permutation=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(permutations[selected].data()));
          alignas(32) uint64_t packed[4];
          _mm256_store_si256(reinterpret_cast<__m256i*>(packed),_mm256_permutevar8x32_epi32(half?b:a,permutation));
          for(unsigned i=0;i<unsigned(std::popcount(selected));++i) {
            Point p;std::memcpy(&p,&packed[i],sizeof(p));*output++=p;
          }
        }
      }
    }
    for (; start < end; ++start) {
      const auto p = points[start];
      if (circle ? circle->contains(p) : p.x >= box.p.x && p.x <= box.q.x && p.y >= box.p.y && p.y <= box.q.y)
        *output++ = p;
    }
  }
};
}  // namespace diskreport::morton_MortonSIMD
