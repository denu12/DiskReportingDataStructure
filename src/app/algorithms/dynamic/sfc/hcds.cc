#include "app/algorithms/dynamic/sfc/sfc.hh"
#include "sfc/HCDS_dynamic.hpp"

namespace diskreport::app::algorithms::dynamic::sfc {
template <template <typename, typename> typename TreeType, typename Input_t, bool hilbert>
struct HCDSDyn {
  using IDX = diskreport::sfc::dynamic::HCDS<TreeType, Input_t, Input_t, hilbert>;
  using PointType = typename IDX::PointType;
  using PT = PointType;
  using QueryType = typename IDX::QueryType;

  using IDXT = Input_t;
  struct Type {
    size_t query_results = 0;
    void handle_deletion(PT p) { index.remove(p); }
    void handle_insertion(PT p) { index.insert(p); }
    IDX index;
    void esa_query(PT lo,PT hi,std::vector<PT>& out) { index.query(lo,hi,std::back_inserter(out)); }
    bool handle_query(std::pair<PT, PT> p) {
      std::vector<PT> out;

      index.query(p.first, p.second, std::back_inserter(out));

      query_results += out.size();
      return true;
    }
    bool valid() { return true; }
    template <template <typename, typename> class MapType, typename StringType>
    Type(MapType<StringType, double> double_params, MapType<StringType, int64_t> int64_params) {}
    size_t size() { return query_results; }
  };
  static constexpr int offset = 0;
};
template <typename A, typename B>
using Absl = absl::btree_multimap<A, B>;
template <typename T>
using HCDSDynQuadAbsl = HCDSDyn<Absl, T, false>;

template <typename T>
using HCDSDynHilbertAbsl = HCDSDyn<Absl, T, true>;
using HCDSDynMemAbsl = DynSFCInMemory<HCDSDynQuadAbsl, uint32_t>;
using HCDSHilbertDynMemAbsl = DynSFCInMemory<HCDSDynHilbertAbsl, uint32_t>;

REGISTER_IMPL_NAMED(HCDSDynMemAbsl, "hcds_dyn");
REGISTER_IMPL_NAMED(HCDSHilbertDynMemAbsl, "hcds_hilbert_dyn");

template <typename A, typename B>
using Std = std::multimap<A, B>;
template <typename T>
using HCDSDynQuadStd = HCDSDyn<Std, T, false>;

template <typename T>
using HCDSDynHilbertStd = HCDSDyn<Std, T, true>;
using HCDSDynMemStd = DynSFCInMemory<HCDSDynQuadStd, uint32_t>;
using HCDSHilbertDynMemStd = DynSFCInMemory<HCDSDynHilbertStd, uint32_t>;

REGISTER_IMPL_NAMED(HCDSDynMemStd, "hcds_dyn_std");
REGISTER_IMPL_NAMED(HCDSHilbertDynMemStd, "hcds_hilbert_dyn_std");

}  // namespace diskreport::app::algorithms::dynamic::sfc