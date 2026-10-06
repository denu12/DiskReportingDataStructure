#include <map>

#include "absl/container/btree_set.h"
#include "app/algorithms/dynamic/sfc/sfc.hh"
#include "sfc/HCDS_dynamic.hpp"

namespace diskreport::app::algorithms::dynamic::sfc {
template <typename Input_t>
struct Naive {
  using IDX = diskreport::sfc::dynamic::HCDS<absl::btree_multimap, Input_t, Input_t, false>;
  using PointType = typename IDX::PointType;
  using PT = PointType;
  using QueryType = typename IDX::QueryType;

  using IDXT = Input_t;
  struct Type {
    size_t query_results = 0;
    void handle_deletion(PT p) { index.erase(p); }
    void handle_insertion(PT p) { index.insert(p); }
    absl::btree_multiset<PointType> index;
    bool handle_query(std::pair<PT, PT> p) {
      auto [l, h] = p;
      // std::vector<PT> out;
      int i = 0;
      for (const auto& px : index) {
        i += (px.x >= l.x & px.y >= l.y & px.x <= h.x & px.y <= h.y);
      }

      query_results += i;  // out.size();
      // std::cout << p.first.x << " " << p.first.y << std::endl;
      // std::cout << p.second.x << " " << p.second.y << std::endl;

      // std::cout << out.size() << std::endl;

      return true;
    }
    bool valid() { return true; }
    template <template <typename, typename> class MapType, typename StringType>
    Type(MapType<StringType, double> double_params, MapType<StringType, int64_t> int64_params) {}
    size_t size() { return query_results; }
  };
  static constexpr int offset = 0;
};
using NaiveI = DynSFCInMemory<Naive, uint32_t>;

REGISTER_IMPL_NAMED(NaiveI, "naive_dyn");

}  // namespace diskreport::app::algorithms::dynamic::sfc