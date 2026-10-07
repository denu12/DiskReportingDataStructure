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
  std::vector<typename IDX::point_y> report_buffer;
  PAM(parlay::sequence<PointType> slice) : index(slice) {}
  PAM(std::vector<PointType>& points)
      : PAM(parlay::sequence<PointType>(points.begin(), points.end())) {}

  void query(const QueryType& q, auto&& out) {
    // Use the public range accumulator, retaining the native count/report semantics.
    report_buffer.resize(index.query_count(q.p.x, q.p.y, q.q.x, q.q.y));
    typename IDX::range_t report({q.p.y, q.p.x}, {q.q.y, q.q.x}, report_buffer.data());
    index.range_tree.range_sum({q.p.x, q.p.y}, {q.q.x, q.q.y}, report);
    for (auto& [y, x] : report_buffer) {
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