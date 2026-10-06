#pragma once
#include <immintrin.h>

#include <execution>
#include "sfc/circle.hh"
namespace diskreport::sfc {
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
  static inline u_int32_t interleave(u_int32_t x, u_int32_t mask) { return _pdep_u32(x, mask); }
};
template <>
struct rank_t<u_int32_t> {
  using type = u_int64_t;
  static inline u_int64_t interleave(u_int64_t x, u_int64_t mask) { return _pdep_u64(x, mask); }
};

template <typename T>
struct Point {
  using ElementType = T;
  T x;
  T y;
  bool operator<(const Point& b) { return x < b.x || (x == b.x && y < b.y); }
};
template <typename PT>
struct Query {
  using PointType = PT;
  PT p, q;
  // double d;
  Query(PointType p, PointType q) : p(p), q(q) {}
  Query(typename PointType::ElementType x, typename PointType::ElementType y,
        typename PointType::ElementType u, typename PointType::ElementType v)
      : p(x, y), q(u, v){};
};
}  // namespace diskreport::sfc