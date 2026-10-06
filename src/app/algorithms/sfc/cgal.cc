#include <boost/foreach.hpp>
#include <boost/property_map/property_map.hpp>
#include <utility>
#include <vector>
//

#include <CGAL/Cartesian.h>
#include <CGAL/Fuzzy_iso_box.h>
#include <CGAL/Kd_tree.h>
#include <CGAL/Range_segment_tree_traits.h>
#include <CGAL/Range_tree_k.h>
#include <CGAL/Search_traits_2.h>

#include "app/algorithms/sfc/sfc.hh"
namespace diskreport::sfc::app::algorithms::sfc::cgal {

template <typename Input_t = uint32_t>
struct CGALRangeTree {
  using IDXT = Input_t;
  using K = CGAL::Cartesian<IDXT>;
  using Traits = CGAL::Range_segment_tree_set_traits_2<K>;
  using IDX = CGAL::Range_tree_2<Traits>;
  using PointType = Traits::Key;
  using QueryType1 = Traits::Interval;
  using QueryType = std::pair<PointType, PointType>;
  IDX index;
  CGALRangeTree(std::vector<PointType>& points) : index(points.begin(), points.end()) {}
  void query(const QueryType& q, auto&& out) {
    index.window_query(QueryType1(q.first, q.second), out);
  }
};
template <typename Input_t = uint32_t>
struct CGALKdTree {
  using IDXT = Input_t;
  using K = CGAL::Cartesian<IDXT>;
  using Traits = CGAL::Search_traits_2<K>;
  using IDX = CGAL::Kd_tree<Traits>;
  using PointType = Traits::Point_d;
  using QueryType1 = CGAL::Fuzzy_iso_box<Traits>;
  using QueryType = std::pair<PointType, PointType>;

  IDX index;
  CGALKdTree(std::vector<PointType>& points) : index(points.begin(), points.end()) {}
  void query(const QueryType& q, auto&& out) { index.search(out, QueryType1(q.first, q.second)); }
};
using CGALRangeTreeImpl = Algo<CGALRangeTree<>, 1>;
using CGALKdTreeImpl = Algo<CGALKdTree<>, 1>;

REGISTER_IMPL_NAMED(CGALRangeTreeImpl, "cgal_rt");
REGISTER_IMPL_NAMED(CGALKdTreeImpl, "cgal_kd");

}  // namespace diskreport::sfc::app::algorithms::sfc::cgal