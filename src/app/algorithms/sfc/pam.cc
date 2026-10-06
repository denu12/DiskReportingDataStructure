#include <sys/types.h>

#include <utility>
#undef LOG
#define PARLAY_SEQUENTIAL
#include <pam/pam.h>

#include "pam_ex/range_utils.h"
//
#include "pam_ex/range_tree.h"
//

//
#include "app/algorithms/sfc/sfc.hh"

namespace diskreport::sfc::app::algorithms::sfc {
template <typename Input_t>
struct PAM {
  using IDXT = Input_t;
  using PointType = ::Point<IDXT, float>;
  using IDX = ::RangeQuery<IDXT, float>;
  struct Query {
    PointType p, q;
    Query(PointType p, PointType q) : p(p), q(q){};
  };
  using QueryType = Query;
  IDX index;
  size_t pnts;
  PAM(parlay::sequence<PointType> slice) : index(slice) {}
  PAM(std::vector<PointType>& points)
      : PAM(parlay::sequence<PointType>(points.begin(), points.end())) {}

  void query(const QueryType& q, auto&& out) {
    auto out2 = index.query_range(q.p.x, q.p.y, q.q.x, q.q.y);
    for (auto& [y, x] : out2) {
      *out = PointType(y, x, 1.0);
    }
  }
};
template <typename Tp>
struct PAMImpl : public Algo<PAM<Tp>> {
  using PK = PAM<Tp>;
  PAMImpl()
      : Algo<PAM<Tp>>([](typename PK::IDXT a, typename PK::IDXT b) {
          return typename PK::PointType(a, b, 1.0);
        }){};
};
using PAMImpl32 = PAMImpl<u_int32_t>;
using PAMImpl16 = PAMImpl<u_int16_t>;
REGISTER_IMPL_NAMED(PAMImpl16, "pam16");

REGISTER_IMPL_NAMED(PAMImpl32, "pam");
}  // namespace diskreport::sfc::app::algorithms::sfc