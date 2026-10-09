// Standalone specialized 3D Morton reporting: C++20, x86-64 AVX2, no external libraries.
// Include this file in a client compiled with -O3 -mavx2. No early-termination oracle.
#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cmath>
#include <cstdint>
#include <immintrin.h>
#include <stdexcept>
#include <utility>
#include <vector>
#if !defined(__AVX2__)
#error "Compile morton3D.cc with -mavx2 on an AVX2-capable x86-64 CPU"
#endif

namespace diskreport::morton3d {
using Wide = unsigned __int128;

// Three uint32 coordinates produce a 96-bit Morton key, stored high word first.
struct MortonCodec3D {
  using Point = std::array<std::uint32_t, 3>;
  using Key = std::array<std::uint64_t, 2>;
  static constexpr std::size_t words = 2;
  static_assert(sizeof(Point) == 12);

  // Spread 21 bits into every third bit of each AVX2 lane.
  static __m256i spread(__m256i x) {
    x = _mm256_and_si256(x, _mm256_set1_epi64x(0x1fffff));
    x = _mm256_and_si256(_mm256_or_si256(x, _mm256_slli_epi64(x,32)), _mm256_set1_epi64x(0x1f00000000ffff));
    x = _mm256_and_si256(_mm256_or_si256(x, _mm256_slli_epi64(x,16)), _mm256_set1_epi64x(0x1f0000ff0000ff));
    x = _mm256_and_si256(_mm256_or_si256(x, _mm256_slli_epi64(x,8)), _mm256_set1_epi64x(0x100f00f00f00f00f));
    x = _mm256_and_si256(_mm256_or_si256(x, _mm256_slli_epi64(x,4)), _mm256_set1_epi64x(0x10c30c30c30c30c3));
    return _mm256_and_si256(_mm256_or_si256(x, _mm256_slli_epi64(x,2)), _mm256_set1_epi64x(0x1249249249249249));
  }
  static __m256i interleave(__m256i x, __m256i y, __m256i z) {
    return _mm256_or_si256(spread(x), _mm256_or_si256(
        _mm256_slli_epi64(spread(y),1), _mm256_slli_epi64(spread(z),2)));
  }
  static std::array<Key,4> encode_four(const Point* p, std::size_t count) {
    const auto offsets = _mm_setr_epi32(0,count>1?3:0,count>2?6:0,count>3?9:0);
    auto axis = [&](unsigned a) { return _mm256_cvtepu32_epi64(
        _mm_i32gather_epi32(reinterpret_cast<const int*>(p->data()+a),offsets,4)); };
    const auto x=axis(0), y=axis(1), z=axis(2);
    const auto upper=interleave(_mm256_srli_epi64(x,21),_mm256_srli_epi64(y,21),_mm256_srli_epi64(z,21));
    const auto low=_mm256_or_si256(interleave(x,y,z),_mm256_slli_epi64(upper,63));
    const auto high=_mm256_srli_epi64(upper,1);
    alignas(32) std::uint64_t lo[4],hi[4];
    _mm256_store_si256(reinterpret_cast<__m256i*>(lo),low);
    _mm256_store_si256(reinterpret_cast<__m256i*>(hi),high);
    std::array<Key,4> result{};
    for(std::size_t lane=0;lane<count;++lane) result[lane]={hi[lane],lo[lane]};
    return result;
  }
  static Key encode(const Point& p) { return encode_four(&p,1)[0]; }
  static std::pair<Key,Key> cell(Key key,unsigned depth) {
    Key lo=key,hi=lo;
    const unsigned suffix=3*(32-depth);
    const auto low_mask=suffix>=64?UINT64_MAX:(std::uint64_t{1}<<suffix)-1;
    const auto high_mask=suffix>64?(std::uint64_t{1}<<(suffix-64))-1:0;
    lo[0]&=~high_mask; lo[1]&=~low_mask;
    hi[0]|=high_mask; hi[1]|=low_mask;
    return {lo,hi};
  }
  static __m256i unsigned_greater(__m256i a,__m256i b) {
    const auto sign=_mm256_set1_epi64x(INT64_MIN);
    return _mm256_cmpgt_epi64(_mm256_xor_si256(a,sign),_mm256_xor_si256(b,sign));
  }
  static bool less(const Key& a,const Key& b) {
    const auto x=_mm_loadu_si128(reinterpret_cast<const __m128i*>(a.data()));
    const auto y=_mm_loadu_si128(reinterpret_cast<const __m128i*>(b.data()));
    const unsigned same=_mm_movemask_pd(_mm_castsi128_pd(_mm_cmpeq_epi64(x,y)));
    if(same==3) return false;
    const unsigned lane=std::countr_zero((~same)&3U);
    const auto sign=_mm_set1_epi64x(INT64_MIN);
    const auto greater=_mm_cmpgt_epi64(_mm_xor_si128(y,sign),_mm_xor_si128(x,sign));
    return (_mm_movemask_pd(_mm_castsi128_pd(greater))>>lane)&1;
  }
};

// Static index. Output iterators receive actual original integer coordinates.
class Morton3D {
  static constexpr std::size_t D = 3;
 public:
  using Codec = MortonCodec3D;
  using Point = typename Codec::Point;
  using Key = typename Codec::Key;
  explicit Morton3D(const std::vector<Point>& input) {
    struct Entry { Key key; std::size_t id; };
    std::vector<Entry> sorted;
    sorted.reserve(input.size());
    for (std::size_t i = 0; i < input.size(); i += 4) {
      const auto count = std::min<std::size_t>(4, input.size() - i);
      const auto keys = Codec::encode_four(input.data() + i, count);
      for (std::size_t lane = 0; lane < count; ++lane) sorted.push_back({keys[lane], i + lane});
    }
    std::sort(sorted.begin(), sorted.end(), [](const Entry& a, const Entry& b) { return Codec::less(a.key, b.key); });
    points_.resize((input.size()+7)/8);
    size_=input.size();
    std::size_t level_size=size_,offset=0;
    offsets_.push_back(0);
    while(level_size>8) {
      const auto blocks=(level_size+7)/8;
      offset+=blocks*8;offsets_.push_back(offset);
      level_size=(blocks+8)/9*8;
    }
    for(auto& axis:ranks_)axis.resize(offset+8,-1);
    for (std::size_t i = 0; i < sorted.size(); ++i) {
      for(unsigned a=0;a<3;++a)points_[i/8].axis[a][i%8]=input[sorted[i].id][a];
      for (std::size_t w = 0; w < Codec::words; ++w) ranks_[w][i] = std::bit_cast<long long>(sorted[i].key[w]);
    }
    for(std::size_t h=1;h<offsets_.size();++h) {
      const auto end=h+1<offsets_.size()?offsets_[h+1]:ranks_[0].size();
      for(std::size_t i=0;i<end-offsets_[h];++i) {
        auto k=(i/8)*9+i%8+1;
        for(std::size_t l=0;l<h-1;++l)k*=9;
        if(k*8<size_)for(unsigned w=0;w<2;++w)ranks_[w][offsets_[h]+i]=ranks_[w][k*8];
      }
    }
  }
  void query(const Point& center, std::uint64_t radius, auto output) const {
    query_squared(center, Wide(radius) * radius, output);
  }
  void query_squared(const Point& center, Wide radius_squared, auto output) const {
    std::uint64_t radius = UINT32_MAX;
    // Integer ceiling square root; larger radii already enclose every axis.
    if (radius_squared < Wide(UINT32_MAX) * UINT32_MAX) {
      radius = std::uint64_t(std::sqrt(static_cast<long double>(radius_squared)));
      // The estimate is only a starting point; these corrections are exact.
      while (Wide(radius) * radius < radius_squared) ++radius;
      while (radius && Wide(radius - 1) * (radius - 1) >= radius_squared) --radius;
    }
    Point lo{}, hi{};
    std::uint32_t diameter = 0;
    for (std::size_t a = 0; a < D; ++a) {
      lo[a] = center[a] > radius ? center[a] - radius : 0;
      hi[a] = std::min<std::uint64_t>(UINT32_MAX, std::uint64_t(center[a]) + radius);
      diameter = std::max(diameter, hi[a] - lo[a]);
    }
    const unsigned suffix = std::bit_width(diameter), depth = 32 - suffix;
    // Only eight possible corners in 3D; noncrossing axes need one choice.
    unsigned crossing=0;
    for(unsigned axis=0;axis<3;++axis)
      if((std::uint64_t(lo[axis])>>suffix)!=(std::uint64_t(hi[axis])>>suffix)) crossing|=1U<<axis;
    std::array<Point,8> corners;
    std::size_t count = 0;
    for(unsigned mask=0;mask<8;++mask) {
      if(mask&~crossing) continue;
      corners[count++] = {mask&1?hi[0]:lo[0],mask&2?hi[1]:lo[1],mask&4?hi[2]:lo[2]};
    }
    std::array<std::pair<Key,Key>,8> ranges;
    for(std::size_t i=0;i<count;i+=4) {
      const auto lanes=std::min<std::size_t>(4,count-i);
      const auto keys=Codec::encode_four(corners.data()+i,lanes);
      for(std::size_t j=0;j<lanes;++j) ranges[i+j]=Codec::cell(keys[j],depth);
    }
    std::sort(ranges.begin(), ranges.begin()+count, [](const auto& a, const auto& b) { return Codec::less(a.first, b.first); });
    for (std::size_t i=0;i<count;++i)
      report(bound(ranges[i].first, false), bound(ranges[i].second, true), center, radius_squared, output);
  }

 private:
  // One coordinate copy, grouped into SIMD-sized blocks.
  struct alignas(32) Block { std::uint32_t axis[3][8]{}; };
  std::vector<Block> points_;
  std::size_t size_;
  std::vector<std::size_t> offsets_;
  std::array<std::vector<long long>, Codec::words> ranks_;

  // Each search node is eight consecutive 96-bit keys, loaded without gathers.
  std::size_t bound(const Key& key, bool upper) const {
    const auto wanted_high=_mm256_set1_epi64x(key[0]),wanted_low=_mm256_set1_epi64x(key[1]);
    auto count=[&](std::size_t offset) {
      unsigned mask=0;
      for(unsigned half=0;half<2;++half) {
        const auto high=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(ranks_[0].data()+offset+half*4));
        const auto low=_mm256_loadu_si256(reinterpret_cast<const __m256i*>(ranks_[1].data()+offset+half*4));
        const auto equal=_mm256_cmpeq_epi64(high,wanted_high);
        auto less=_mm256_or_si256(Codec::unsigned_greater(wanted_high,high),
            _mm256_and_si256(equal,Codec::unsigned_greater(wanted_low,low)));
        if(upper)less=_mm256_or_si256(less,_mm256_and_si256(equal,_mm256_cmpeq_epi64(low,wanted_low)));
        mask|=unsigned(_mm256_movemask_pd(_mm256_castsi256_pd(less)))<<(4*half);
      }
      return std::size_t(std::popcount(mask));
    };
    std::size_t k=0;
    for(std::size_t h=offsets_.size()-1;h>0;--h)k=k*9+count(offsets_[h]+k)*8;
    return k+count(k);
  }
  void report(std::size_t first, std::size_t last, const Point& center,
              Wide radius_squared, auto& output) const {
    const auto radius_lo = _mm256_set1_epi64x(std::uint64_t(radius_squared));
    const auto radius_hi = _mm256_set1_epi64x(std::uint64_t(radius_squared >> 64));
    // Aligned coordinate blocks avoid gathers. Mask out points outside the interval.
    for(std::size_t block=first/8;block<(last+7)/8;++block) {
      const auto begin=std::max(first,block*8)-block*8;
      const auto end=std::min(last,block*8+8)-block*8;
      const unsigned valid=((1U<<end)-1)^((1U<<begin)-1);
      __m256i sums[2]{_mm256_setzero_si256(),_mm256_setzero_si256()};
      __m256i carries[2]{_mm256_setzero_si256(),_mm256_setzero_si256()};
      for(unsigned axis=0;axis<3;++axis) {
        const auto values=_mm256_load_si256(reinterpret_cast<const __m256i*>(points_[block].axis[axis]));
        const auto c=_mm256_set1_epi32(center[axis]);
        const auto delta=_mm256_sub_epi32(_mm256_max_epu32(values,c),_mm256_min_epu32(values,c));
        const __m256i halves[2]{_mm256_cvtepu32_epi64(_mm256_castsi256_si128(delta)),
                               _mm256_cvtepu32_epi64(_mm256_extracti128_si256(delta,1))};
        for(unsigned half=0;half<2;++half) {
          const auto term=_mm256_mul_epu32(halves[half],halves[half]),previous=sums[half];
          sums[half]=_mm256_add_epi64(sums[half],term);
          carries[half]=_mm256_sub_epi64(carries[half],Codec::unsigned_greater(previous,sums[half]));
        }
      }
      unsigned mask=0;
      for(unsigned half=0;half<2;++half) {
        const auto inside=_mm256_or_si256(Codec::unsigned_greater(radius_hi,carries[half]),
            _mm256_and_si256(_mm256_cmpeq_epi64(carries[half],radius_hi),
                _mm256_xor_si256(Codec::unsigned_greater(sums[half],radius_lo),_mm256_set1_epi64x(-1))));
        mask|=unsigned(_mm256_movemask_pd(_mm256_castsi256_pd(inside)))<<(4*half);
      }
      mask&=valid;
      while(mask) {
        const auto lane=std::countr_zero(mask);
        *output++=Point{points_[block].axis[0][lane],points_[block].axis[1][lane],points_[block].axis[2][lane]};
        mask&=mask-1;
      }
    }
  }
};
}  // namespace diskreport::morton3d
