// Standalone d-dimensional Morton reporting: C++20, x86-64 AVX2, no external libraries.
// Include this file in a client compiled with -O3 -mavx2. No early-termination oracle.
#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <immintrin.h>
#include <stdexcept>
#include <utility>
#include <vector>
#if !defined(__AVX2__)
#error "Compile morton_d_dim.cc with -mavx2 on an AVX2-capable x86-64 CPU"
#endif

namespace diskreport::ddim {
using Wide = unsigned __int128;

// Original interleaving: coordinate bit b on axis a occupies rank bit D*b+a.
// The most significant rank word comes first; padding words remain zero.
template<std::size_t D> struct Morton {
  static_assert(D >= 1 && D <= 16, "MortonDDim supports 1 through 16 dimensions: cell enumeration is exponential in D");
  using Point = std::array<std::uint32_t, D>;
  static_assert(sizeof(Point) == D * sizeof(std::uint32_t));
  static constexpr std::size_t bits = 32 * D;
  static constexpr std::size_t words = (bits + 63) / 64;
  using Key = std::array<std::uint64_t, (words + 3) / 4 * 4>;

  // Encode four points in parallel; unused lanes repeat the first point safely.
  static std::array<Key, 4> encode_four(const Point* points, std::size_t count,
                                      unsigned depth = 32) {
    if (depth > 32 || count == 0 || count > 4) throw std::invalid_argument("Invalid encoding input");
    const auto offsets = _mm_setr_epi32(0, count > 1 ? D : 0,
                                       count > 2 ? 2 * D : 0, count > 3 ? 3 * D : 0);
    alignas(32) __m256i coordinates[D];
    for (std::size_t a = 0; a < D; ++a) {
      const auto values = _mm_i32gather_epi32(reinterpret_cast<const int*>(points->data() + a), offsets, 4);
      coordinates[a] = _mm256_cvtepu32_epi64(values);
    }
    std::array<Key, 4> result{};
    const auto one = _mm256_set1_epi64x(1);
    for (std::size_t word = 0; word < words; ++word) {
      auto packed = _mm256_setzero_si256();
      const auto first_bit = (words - 1 - word) * 64;
      for (std::size_t k = first_bit; k < std::min(bits, first_bit + 64); ++k) {
        const unsigned b = k / D;
        if (b < 32 - depth) continue;
        const auto bit = _mm256_and_si256(_mm256_srlv_epi64(coordinates[k % D], _mm256_set1_epi64x(b)), one);
        packed = _mm256_or_si256(packed, _mm256_sllv_epi64(bit, _mm256_set1_epi64x(k % 64)));
      }
      alignas(32) std::uint64_t lanes[4];
      _mm256_store_si256(reinterpret_cast<__m256i*>(lanes), packed);
      for (std::size_t lane = 0; lane < count; ++lane) result[lane][word] = lanes[lane];
    }
    return result;
  }
  static Key encode(const Point& point, unsigned depth = 32) {
    return encode_four(&point, 1, depth)[0];
  }
  static std::pair<Key, Key> cell(const Point& point, unsigned depth) {
    Key lo = encode(point, depth), hi = lo;
    const std::size_t suffix_bits = D * (32 - depth);
    for (std::size_t w = 0; w < words; ++w) {
      const auto first_bit = (words - 1 - w) * 64;
      const auto count = suffix_bits > first_bit ? std::min<std::size_t>(64, suffix_bits - first_bit) : 0;
      hi[w] |= count == 64 ? UINT64_MAX : (std::uint64_t{1} << count) - 1;
    }
    return {lo, hi};
  }
  static __m256i unsigned_greater(__m256i a, __m256i b) {
    const auto sign = _mm256_set1_epi64x(INT64_MIN);
    return _mm256_cmpgt_epi64(_mm256_xor_si256(a, sign), _mm256_xor_si256(b, sign));
  }
  static bool less(const Key& a, const Key& b) {
    // SIMD lexicographic comparison, four rank words at a time.
    for (std::size_t w = 0; w < a.size(); w += 4) {
      const auto x = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(a.data() + w));
      const auto y = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(b.data() + w));
      const unsigned same = _mm256_movemask_pd(_mm256_castsi256_pd(_mm256_cmpeq_epi64(x, y)));
      if (same != 15) {
        const unsigned lane = std::countr_zero((~same) & 15U);
        return (_mm256_movemask_pd(_mm256_castsi256_pd(unsigned_greater(y, x))) >> lane) & 1;
      }
    }
    return false;
  }
};

// Static index. Output iterators receive actual original integer coordinates.
template<std::size_t D> class MortonDDim {
 public:
  using Codec = Morton<D>;
  using Point = typename Codec::Point;
  using Key = typename Codec::Key;
  explicit MortonDDim(const std::vector<Point>& input) {
    struct Entry { Key key; std::size_t id; };
    std::vector<Entry> sorted;
    sorted.reserve(input.size());
    for (std::size_t i = 0; i < input.size(); i += 4) {
      const auto count = std::min<std::size_t>(4, input.size() - i);
      const auto keys = Codec::encode_four(input.data() + i, count);
      for (std::size_t lane = 0; lane < count; ++lane) sorted.push_back({keys[lane], i + lane});
    }
    std::sort(sorted.begin(), sorted.end(), [](const Entry& a, const Entry& b) { return Codec::less(a.key, b.key); });
    points_.resize(input.size());
    for (auto& axis : ranks_) axis.resize(input.size());
    for (std::size_t i = 0; i < sorted.size(); ++i) {
      points_[i] = input[sorted[i].id];
      for (std::size_t w = 0; w < Codec::words; ++w) ranks_[w][i] = std::bit_cast<long long>(sorted[i].key[w]);
    }
  }
  void query(const Point& center, std::uint64_t radius, auto output) const {
    query_squared(center, Wide(radius) * radius, output);
  }
  void query_squared(const Point& center, Wide radius_squared, auto output) const {
    std::uint64_t radius = UINT32_MAX;
    // Integer ceiling square root; larger radii already enclose every axis.
    if (radius_squared < Wide(UINT32_MAX) * UINT32_MAX) {
      std::uint64_t lo = 0, hi = UINT32_MAX;
      while (lo < hi) {
        const auto mid = lo + (hi - lo) / 2;
        if (Wide(mid) * mid < radius_squared) lo = mid + 1;
        else hi = mid;
      }
      radius = lo;
    }
    Point lo{}, hi{};
    std::uint32_t diameter = 0;
    for (std::size_t a = 0; a < D; ++a) {
      lo[a] = center[a] > radius ? center[a] - radius : 0;
      hi[a] = std::min<std::uint64_t>(UINT32_MAX, std::uint64_t(center[a]) + radius);
      diameter = std::max(diameter, hi[a] - lo[a]);
    }
    const unsigned suffix = std::bit_width(diameter), depth = 32 - suffix;
    // At most 2^D coarse cells; D is deliberately capped at 16.
    std::vector<std::pair<Key, Key>> ranges;
    Point corner = lo;
    auto visit = [&](auto&& self, std::size_t axis) -> void {
      if (axis == D) { ranges.push_back(Codec::cell(corner, depth)); return; }
      corner[axis] = lo[axis];
      self(self, axis + 1);
      if ((std::uint64_t(lo[axis]) >> suffix) != (std::uint64_t(hi[axis]) >> suffix)) {
        corner[axis] = hi[axis];
        self(self, axis + 1);
      }
    };
    visit(visit, 0);
    std::sort(ranges.begin(), ranges.end(), [](const auto& a, const auto& b) { return Codec::less(a.first, b.first); });
    for (const auto& [first, last] : ranges)
      report(bound(first, false), bound(last, true), center, radius_squared, output);
  }
 private:
  std::vector<Point> points_;
  std::array<std::vector<long long>, Codec::words> ranks_;

  // Compare four probe ranks in parallel, across every Morton word.
  unsigned compare_four(const std::array<std::size_t, 4>& positions, const Key& key, bool upper) const {
    const auto offsets = _mm256_setr_epi64x(positions[0], positions[1], positions[2], positions[3]);
    auto equal = _mm256_set1_epi64x(-1), less = _mm256_setzero_si256();
    for (std::size_t w = 0; w < Codec::words; ++w) {
      const auto values = _mm256_i64gather_epi64(ranks_[w].data(), offsets, 8);
      const auto wanted = _mm256_set1_epi64x(key[w]);
      less = _mm256_or_si256(less, _mm256_and_si256(equal, Codec::unsigned_greater(wanted, values)));
      equal = _mm256_and_si256(equal, _mm256_cmpeq_epi64(values, wanted));
    }
    if (upper) less = _mm256_or_si256(less, equal);
    return _mm256_movemask_pd(_mm256_castsi256_pd(less));
  }
  std::size_t bound(const Key& key, bool upper) const {
    std::size_t lo = 0, hi = points_.size();
    while (hi - lo >= 4) {
      const auto span = hi - lo;
      const std::array<std::size_t, 4> pivots{lo + span / 5, lo + 2 * span / 5,
                                           lo + 3 * span / 5, lo + 4 * span / 5};
      const auto count = std::popcount(compare_four(pivots, key, upper));
      if (count) lo = pivots[count - 1] + 1;
      if (count < 4) hi = pivots[count];
    }
    while (lo < hi && (compare_four({lo, lo, lo, lo}, key, upper) & 1)) ++lo;
    return lo;
  }
  static Point copy_point(const Point& source) {
    Point target; std::size_t a = 0;
    for (; D - a >= 8; a += 8)
      _mm256_storeu_si256(reinterpret_cast<__m256i*>(target.data() + a),
                         _mm256_loadu_si256(reinterpret_cast<const __m256i*>(source.data() + a)));
    if (D - a >= 4) {
      _mm_storeu_si128(reinterpret_cast<__m128i*>(target.data() + a),
                      _mm_loadu_si128(reinterpret_cast<const __m128i*>(source.data() + a))); a += 4;
    }
    if (D - a >= 2) {
      _mm_storel_epi64(reinterpret_cast<__m128i*>(target.data() + a),
                      _mm_loadl_epi64(reinterpret_cast<const __m128i*>(source.data() + a))); a += 2;
    }
    if (a < D) target[a] = source[a];
    return target;
  }
  void report(std::size_t first, std::size_t last, const Point& center,
              Wide radius_squared, auto& output) const {
    const auto radius_lo = _mm256_set1_epi64x(std::uint64_t(radius_squared));
    const auto radius_hi = _mm256_set1_epi64x(std::uint64_t(radius_squared >> 64));
    for (std::size_t i = first; i < last; i += 4) {
      const auto count = std::min<std::size_t>(4, last - i);
      const auto offsets = _mm_setr_epi32(0, count > 1 ? D : 0, count > 2 ? 2 * D : 0, count > 3 ? 3 * D : 0);
      auto sum = _mm256_setzero_si256(), carry = _mm256_setzero_si256();
      for (std::size_t a = 0; a < D; ++a) {
        const auto values = _mm_i32gather_epi32(reinterpret_cast<const int*>(points_[i].data() + a), offsets, 4);
        const auto c = _mm_set1_epi32(center[a]);
        const auto delta = _mm256_cvtepu32_epi64(_mm_sub_epi32(_mm_max_epu32(values, c), _mm_min_epu32(values, c)));
        const auto term = _mm256_mul_epu32(delta, delta), previous = sum;
        sum = _mm256_add_epi64(sum, term);
        carry = _mm256_sub_epi64(carry, Codec::unsigned_greater(previous, sum));
      }
      const auto inside = _mm256_or_si256(Codec::unsigned_greater(radius_hi, carry),
          _mm256_and_si256(_mm256_cmpeq_epi64(carry, radius_hi),
                          _mm256_xor_si256(Codec::unsigned_greater(sum, radius_lo), _mm256_set1_epi64x(-1))));
      unsigned mask = _mm256_movemask_pd(_mm256_castsi256_pd(inside)) & ((1U << count) - 1);
      while (mask) {
        const auto lane = std::countr_zero(mask);
        *output++ = copy_point(points_[i + lane]);
        mask &= mask - 1;
      }
    }
  }
};
}  // namespace diskreport::ddim
