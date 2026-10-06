#pragma once
#include <immintrin.h>
#include <x86intrin.h>

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <vector>
#pragma GCC optimize("O3")
#pragma GCC target("avx2,bmi")
template <typename>
struct Reg {};
template <>
struct Reg<int> {
  using type = __m256i;
  static inline type load(int* x) { return _mm256_load_si256((type*)x); }
  static inline type cmpgt(type a, type b) { return _mm256_cmpgt_epi32(a, b); }
  static inline unsigned permuted_count(type ca, type cb) {
    auto c = _mm256_packs_epi32(ca, cb);
    int mask = _mm256_movemask_epi8(c);
    // we need to divide the result by two because we call movemask_epi8 on 16-bit masks:
    return __tzcnt_u32(mask) >> 1;
  }
  static inline unsigned direct_count(type ca, type cb) {
    int mb = _mm256_movemask_ps((__m256)cb);
    int ma = _mm256_movemask_ps((__m256)ca);

    unsigned mask = (1 << 16);
    mask |= mb << 8;
    mask |= ma;

    return __tzcnt_u32(mask);
  }
  static inline void permute(int* node) {
    const auto perm = _mm256_setr_epi32(4, 5, 6, 7, 0, 1, 2, 3);
    auto* middle = (type*)(node + 4);
    auto x = _mm256_loadu_si256(middle);
    x = _mm256_permutevar8x32_epi32(x, perm);
    _mm256_storeu_si256(middle, x);
  }
  static constexpr bool permuting = true;

  static inline __m256i set(int val) { return _mm256_set1_epi32(val); }

  static constexpr int stride = 8;
  static constexpr auto alignment = 32;  // alignment in byte (2MB)
};
template <>
struct Reg<uint32_t> {
  using type = __m256i_u;
  static inline type load(uint32_t* x) { return _mm256_load_si256((type*)x); }
  static inline __mmask8 cmpgt(type a, type b) {
    // Flip the sign bit so signed AVX2 comparison orders unsigned values.
    const auto sign = _mm256_set1_epi32(INT32_MIN);
    return _mm256_movemask_ps(_mm256_castsi256_ps(_mm256_cmpgt_epi32(
        _mm256_xor_si256(a, sign), _mm256_xor_si256(b, sign))));
  }
  static inline unsigned permuted_count(__mmask8 ca, __mmask8 cb) {
    // auto c = _mm256_packs_epi32(ca, cb);
    // int mask = _mm256_movemask_epi8(c);
    // we need to divide the result by two because we call movemask_epi8 on 16-bit masks:
    return direct_count(ca, cb);
  }
  static inline unsigned direct_count(__mmask8 ca, __mmask8 cb) {
    unsigned mask = (1 << 16);
    mask |= cb << 8;
    mask |= ca;

    return __tzcnt_u32(mask);
  }
  static constexpr bool permuting = false;
  static inline void permute(uint32_t* bnode) {
    // no permute needed
  }
  static inline type set(uint32_t val) { return _mm256_set1_epi32(val); }

  static constexpr int stride = 8;
  static constexpr auto alignment = 32;  // alignment in byte (2MB)
};
template <>
struct Reg<uint64_t> {
  struct type { __m256i low, high; };
  static inline type load(uint64_t* x) {
    return {_mm256_load_si256(reinterpret_cast<const __m256i*>(x)),
            _mm256_load_si256(reinterpret_cast<const __m256i*>(x + 4))};
  }
  static inline __mmask8 cmpgt(type a, type b) {
    const auto sign = _mm256_set1_epi64x(INT64_MIN);
    const auto low = _mm256_cmpgt_epi64(_mm256_xor_si256(a.low, sign),
                                     _mm256_xor_si256(b.low, sign));
    const auto high = _mm256_cmpgt_epi64(_mm256_xor_si256(a.high, sign),
                                      _mm256_xor_si256(b.high, sign));
    return _mm256_movemask_pd(_mm256_castsi256_pd(low)) |
           (_mm256_movemask_pd(_mm256_castsi256_pd(high)) << 4);
  }
  static inline unsigned permuted_count(__mmask8 ca, __mmask8 cb) {
    // auto c = _mm256_packs_epi32(ca, cb);
    // int mask = _mm256_movemask_epi8(c);
    // we need to divide the result by two because we call movemask_epi8 on 16-bit masks:
    return direct_count(ca, cb);
  }
  static inline unsigned direct_count(__mmask8 ca, __mmask8 cb) {
    unsigned mask = (1 << 16);
    mask |= cb << 8;
    mask |= ca;

    return __tzcnt_u32(mask);
  }
  static inline void permute(uint64_t* bnode) {
    // no permute needed
  }
  static constexpr bool permuting = false;
  static inline type set(uint64_t val) {
    const auto lanes = _mm256_set1_epi64x(val);
    return {lanes, lanes};
  }

  static constexpr int stride = 8;
  static constexpr auto alignment = 32;  // alignment in byte (2MB)
};
template <typename ValueType>
unsigned permuted_rank(typename Reg<ValueType>::type x, ValueType* y) {
  auto a = Reg<ValueType>::load(y);
  auto b = Reg<ValueType>::load((y + Reg<ValueType>::stride));

  auto ca = Reg<ValueType>::cmpgt(a, x);
  auto cb = Reg<ValueType>::cmpgt(b, x);

  return Reg<ValueType>::permuted_count(ca, cb);
}
template <typename ValueType>
size_t direct_rank(typename Reg<ValueType>::type x, ValueType* y) {
  auto a = Reg<ValueType>::load(y);
  auto b = Reg<ValueType>::load((y + Reg<ValueType>::stride));

  auto ca = Reg<ValueType>::cmpgt(a, x);
  auto cb = Reg<ValueType>::cmpgt(b, x);

  return Reg<ValueType>::direct_count(ca, cb);
}
constexpr unsigned int BAsPower2 = 4;
constexpr unsigned int BAsValue = 1 << BAsPower2;
template <typename ValueType, typename IndexType = unsigned>
struct ImplicitStaticBPlusTree {
  ValueType* btree;
  ~ImplicitStaticBPlusTree() { delete btree; }
  const IndexType N;
  const IndexType H;
  const IndexType S;
  ValueType operator[](size_t i) { return btree[i]; }
  static constexpr IndexType blocks(IndexType n) { return (n + BAsValue - 1) >> BAsPower2; }
  static constexpr IndexType prev_keys(IndexType n) {
    return (blocks(n) + BAsValue) / (BAsValue + 1) << BAsPower2;
  }
  // height of a balanced n-key B+ tree
  static constexpr IndexType height(IndexType n) {
    return (n <= BAsValue ? 1 : height(prev_keys(n)) + 1);
  }
  std::vector<IndexType> offsets;
  IndexType offset2(IndexType h) {
    IndexType k = 0, n = N;
    IndexType h2 = h;
    while (h2--) {
      k += blocks(n) << BAsPower2;
      n = prev_keys(n);
    }
    return k;
  }
  IndexType T;
  static constexpr ValueType max_value = std::numeric_limits<ValueType>::max();
  explicit ImplicitStaticBPlusTree(size_t N) : N(N), H(height(N)), S(offset2(height(N))) {
    offsets.resize(H + 1);

    for (int i = 0; i <= H; i++) {
      offsets[i] = offset2(i);
    }
    T = ((sizeof(ValueType) * S + Reg<ValueType>::alignment - 1) / Reg<ValueType>::alignment) *
        Reg<ValueType>::alignment;
    btree = new (std::align_val_t(64)) ValueType[T];
    // btree = (ValueType*)std::aligned_alloc(32, T);
  }
  explicit ImplicitStaticBPlusTree(const std::vector<ValueType>& vec)
      : ImplicitStaticBPlusTree(vec.size()) {
    memcpy(btree, vec.data(), sizeof(ValueType) * vec.size());
    build();
  }

  void build() {
    // copy
    // std::copy(vec.begin(), vec.end(), btree);

    // pad
    for (IndexType i = N; i < S; i++) {
      btree[i] = max_value;
    }  // finished building
    for (IndexType h = 1; h < H; h++) {
      for (IndexType i = 0; i < offsets[h + 1] - offsets[h]; i++) {
        // i = k * B + j
        int k = (i >> BAsPower2), j = i - (k << BAsPower2);
        k = k * (BAsValue + 1) + j + 1;  // compare to the right of the key
        // and then always to the left
        for (IndexType l = 0; l < h - 1; l++) k *= (BAsValue + 1);
        // pad the rest with infinities if the key doesn't exist
        btree[offsets[h] + i] = ((k << BAsPower2) < N ? btree[k << BAsPower2] : max_value);
      }
    }
    if constexpr (Reg<ValueType>::permuting) {
      for (IndexType i = offsets[1]; i < S; i += BAsValue) Reg<ValueType>::permute(btree + i);
    }
  }
  // auto lower_bound(size_t start, ValueType _x) {
  //   size_t k = 0;  // we assume k already multiplied by B to optimize pointer arithmetic
  //   auto x = Reg<ValueType>::set(_x - 1);
  //   for (size_t h = H - 1; h > 0; h--) {
  //     size_t i = permuted_rank(x, btree + offsets[h] + k);
  //     k = k * (BAsValue + 1) + (i << BAsPower2);
  //   }
  //   size_t i = direct_rank(x, btree + k);
  //   auto result = (k + i);
  //   if (result > N) {
  //     result = 0UL;
  //   }
  //   if (result <= start) {
  //     return start;
  //   }
  //   return result;
  // }
  // auto upper_bound(size_t start, ValueType _x) {
  //   size_t k = 0;  // we assume k already multiplied by B to optimize pointer arithmetic
  //   auto x = Reg<ValueType>::set(_x);
  //   for (int h = H - 1; h > 0; h--) {
  //     size_t i = permuted_rank(x, btree + offsets[h] + k);
  //     k = k * (BAsValue + 1) + (i << BAsPower2);
  //   }
  //   size_t i = direct_rank(x, btree + k);
  //   return std::min((k + i) > start ? (k + i) : start, N);
  // }
  auto lower_bound2(ValueType _x) {
    IndexType k = 0;  // we assume k already multiplied by B to optimize pointer arithmetic
    auto x = Reg<ValueType>::set(_x - 1);
    for (IndexType h = H - 1; h > 0; h--) {
      IndexType i = permuted_rank(x, btree + offsets[h] + k);
      k = k * (BAsValue + 1) + (i << BAsPower2);
    }
    IndexType i = direct_rank(x, btree + k);
    auto result = (k + i);
    if (result > N) {
      result = 0UL;
    }
    return result;
  }
  auto upper_bound2(ValueType _x) {
    IndexType k = 0;  // we assume k already multiplied by B to optimize pointer arithmetic
    auto x = Reg<ValueType>::set(_x);
    for (IndexType h = H - 1; h > 0; h--) {
      IndexType i = permuted_rank(x, btree + offsets[h] + k);
      k = k * (BAsValue + 1) + (i << BAsPower2);
    }
    IndexType i = direct_rank(x, btree + k);
    return std::min(k + i, N);
  }
};
/*
constexpr auto B = BAsValue;
template <typename ValueType>
struct StaticBTree {
  std::vector<ValueType> vals;
  int nblocks;
  ValueType* btree;
  static constexpr ValueType max_value = std::numeric_limits<ValueType>::max();
  explicit StaticBTree(const std::vector<ValueType>& vec) : vals(vec) {
    nblocks = (vals.size() + B - 1) / B;
    btree = new ValueType[nblocks * B];
    build();
  }

  int go(int k, int i) { return k * (B + 1) + i + 1; }
  size_t t = 0;

  void build(int k = 0) {
    if (k < nblocks) {
      for (int i = 0; i < B; i++) {
        build(go(k, i));
        btree[k * B + i] = (t < vals.size() ? vals[t++] : max_value);
      }
      build(go(k, B));
    }
  }
  auto lower_bound(int _x) {
    int k = 0;
    ValueType res = max_value;
    auto x = set_full(_x);
    while (k < nblocks) {
      int mask = ~(cmp(x, &btree[k * B + 0]) + (cmp(x, &btree[k * B + 8]) << 8));
      int i = __builtin_ffs(mask) - 1;
      if (i < B) res = btree[k * B + i];
      k = go(k, i);
    }
    return res;
  }
};*/
