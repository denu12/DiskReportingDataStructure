#include <sys/types.h>

#include <utility>
#undef LOG
#define PARLAY_SEQUENTIAL
#include "app/algorithms/static/adapter.hh"
#include "cpdd/basic_point.h"
#include "cpdd/cpdd.h"

namespace diskreport::sfc::app::algorithms::sfc {
template <typename Input_t>
struct Pkd {
  using IDXT = Input_t;
  using PointType = cpdd::PointType<IDXT, 2>;
  using QueryType = std::pair<PointType, PointType>;
  using tree = cpdd::ParallelKDtree<PointType>;
  tree index;
  size_t pnts;
  parlay::sequence<PointType> outs;
  Pkd(std::vector<PointType>& points) {
    auto slice = parlay::make_slice(points.data(), points.data() + points.size());
    index.build(slice, 2);
    pnts = points.size();
  }
  void query(const QueryType& q, auto&& out) {
    size_t i, k;
    auto siz = index.range_count(q, i, k);  // TODO discuss
    outs.resize(siz);
    size_t s = index.range_query_serial(q, outs);
    for (auto s : outs) {
      *(out++) = s;
    }
  }
};
template <typename Tp>
struct PkdImpl : public Algo<Pkd<Tp>> {
  using PK = Pkd<Tp>;
  PkdImpl()
      : Algo<Pkd<Tp>>([](typename PK::IDXT a, typename PK::IDXT b) {
          return typename PK::PointType({a, b});
        }){};
};
using PkdImpl32 = PkdImpl<u_int32_t>;
REGISTER_IMPL_NAMED(PkdImpl32, "pkd");
using PkdImpl16 = PkdImpl<u_int16_t>;
REGISTER_IMPL_NAMED(PkdImpl16, "pkd16");
}  // namespace diskreport::sfc::app::algorithms::sfc