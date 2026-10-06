#include <sys/types.h>

#include <utility>
#undef LOG
#define PARLAY_SEQUENTIAL
#include <array>

#include "pargeo/kdTree.h"
#include "pargeo/kdTreeRange.h"
//

//
#include "app/algorithms/sfc/sfc.hh"

namespace diskreport::sfc::app::algorithms::sfc {
namespace {
template <int dim, typename nodeT, typename objT>
void rangeHelper(nodeT* tree, objT qMin, objT qMax, parlay::sequence<size_t>& out, objT* A) {
  int relation = tree->boxCompare(qMin, qMax, tree->getMin(), tree->getMax());

  if (relation == tree->boxExclude) {
    return;
  } else if (relation == tree->boxInclude) {
    for (size_t i = 0; i < tree->size(); ++i) {
      objT* p = tree->getItem(i);
      out.push_back(p - A);
    }
  } else {  // intersect
    if (tree->isLeaf()) {
      for (size_t i = 0; i < tree->size(); ++i) {
        objT* p = tree->getItem(i);

        if (qMin.x[0] <= p->x[0] && qMin.x[1] <= p->x[1] && qMax.x[0] >= p->x[0] &&
            qMax.x[1] >= p->x[1])
          out.push_back(p - A);
      }
    } else {
      rangeHelper<dim, nodeT, objT>(tree->L(), qMin, qMax, out, A);
      rangeHelper<dim, nodeT, objT>(tree->R(), qMin, qMax, out, A);
    }
  }
}
}  // namespace
template <typename Input_t>
struct Pargeo {
  using IDXT = Input_t;
  using PointType = pargeo::_point<2, IDXT, pargeo::_empty, pargeo::_empty>;
  using nodeT = pargeo::kdNode<2, PointType>;
  struct Query {
    PointType p, q;
    Query(PointType p, PointType q) : p(p), q(q){};
  };
  using QueryType = Query;
  size_t pnts;
  parlay::sequence<PointType> points;
  nodeT* index;

  Pargeo(parlay::sequence<PointType> slice) : points(slice) {
    index = pargeo::buildKdt<2, PointType>(points, false, false);
  }
  Pargeo(std::vector<PointType>& points2)
      : Pargeo(parlay::sequence<PointType>(points2.begin(), points2.end())) {}

  void query(const QueryType& q, auto&& out) {
    auto out2 = parlay::sequence<size_t>();

    rangeHelper<2, pargeo::kdNode<2, PointType>, PointType>(index, q.p, q.q, out2, points.data());
    for (auto s : out2) {
      out = points[s];
    }
  }
};
template <typename Tp>
struct PargeoImpl : public Algo<Pargeo<Tp>> {
  using PK = Pargeo<Tp>;
  PargeoImpl()
      : Algo<Pargeo<Tp>>([](typename PK::IDXT a, typename PK::IDXT b) {
          std::array<typename PK::IDXT, 2> data = {a, b};
          return typename PK::PointType(data.data());
        }){};
};
using PargeoImpl32 = PargeoImpl<u_int32_t>;
using PargeoImpl16 = PargeoImpl<u_int16_t>;
REGISTER_IMPL_NAMED(PargeoImpl16, "pargeo16");

REGISTER_IMPL_NAMED(PargeoImpl32, "pargeo");
}  // namespace diskreport::sfc::app::algorithms::sfc