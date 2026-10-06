#pragma once
#include "app/algorithms/sfc/sfc.hh"

namespace diskreport::sfc::app::algorithms::sfc {
template <typename Input_t, typename Key_t = Input_t>
struct Naive {
  using IDXT = Input_t;
  using PointType = Point<Input_t>;
  using QueryType = Query<PointType>;
  std::vector<PointType> index;
  Naive(const std::vector<PointType>& points) : index(points) {}
  void query(const QueryType& q, auto&& out) {
    for (auto& n : index) {
      if (n.x >= q.p.x && n.y >= q.p.y && n.x <= q.q.x && n.y <= q.q.y) {
        *out = n;
      }
    }
  }
};
}  // namespace diskreport::sfc::app::algorithms::sfc