#include <sys/types.h>

#include "app/algorithms/sfc/sfc.hh"
#include "sfc/SHCDS.hh"

#undef HWY_TARGET_INCLUDE
// For dynamic dispatch, specify the name of the current file (unfortunately
// __FILE__ is not reliable) so that foreach_target.h can re-include it.
#define HWY_TARGET_INCLUDE "app/algorithms/sfc/hcds.cc"
// Generates code for each enabled target by re-including this source file.

#include "hwy/foreach_target.h"  // IWYU pragma: keep
#include "sfc/HCDS.hpp"
#include "static_btree/static_btree.hh"

HWY_BEFORE_NAMESPACE();
namespace diskreport::sfc::app::algorithms::sfc {
namespace HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;
template <typename DT>
using LB = ::diskreport::static_btree::HWY_NAMESPACE::ImplicitStaticBTree<DT>;
bool RegisterAll(const std::string& suffix) {
  std::string target_name = hwy::TargetName(HWY_TARGET);
  std::cout << suffix << " " << target_name << " " << LB<u_int64_t>::B << std::endl;
  std::string hilbert = "hcds_hilbert:";
  std::string normal = "hcds:";
  using HCDSAlgoHilbert = Algo<diskreport::sfc::HWY_NAMESPACE::HCDS<LB, u_int32_t, u_int32_t, true>>;
  using HCDSAlgo = Algo<diskreport::sfc::HWY_NAMESPACE::HCDS<LB, u_int32_t, u_int32_t, false>>;
  return diskreport::app::algorithms::registerImpl<HCDSAlgoHilbert>(hilbert + suffix) &&
         diskreport::app::algorithms::registerImpl<HCDSAlgo>(normal + suffix);
}
}  // namespace HWY_NAMESPACE
}  // namespace diskreport::sfc::app::algorithms::sfc
HWY_AFTER_NAMESPACE();
#if HWY_ONCE
namespace diskreport::sfc::app::algorithms::sfc {

// using HCDSAlgoHilbert16 = Algo<diskreport::sfc::HCDS<u_int16_t, u_int16_t, true>>;
// using HCDSAlgo16 = Algo<diskreport::sfc::HCDS<u_int16_t, u_int16_t, false>>;
// REGISTER_IMPL_NAMED(HCDSAlgoHilbert16, "hcds_hilbert16");
// REGISTER_IMPL_NAMED(HCDSAlgo16, "hcds16");

using SHCDSAlgoHilbert = Algo<diskreport::sfc::SHCDS<u_int32_t, u_int32_t, true>>;
using SHCDSAlgo = Algo<diskreport::sfc::SHCDS<u_int32_t, u_int32_t, false>>;
REGISTER_IMPL_NAMED(SHCDSAlgoHilbert, "shcds_hilbert");
REGISTER_IMPL_NAMED(SHCDSAlgo, "shcds");
HWY_EXPORT(RegisterAll);
bool registerRuntime() {
  HWY_DYNAMIC_DISPATCH(RegisterAll)("best");
  for (int64_t target : hwy::SupportedAndGeneratedTargets()) {
    hwy::SetSupportedTargetsForTest(target);
    HWY_DYNAMIC_DISPATCH(RegisterAll)(hwy::TargetName(target));
  }
  hwy::SetSupportedTargetsForTest(0);

  return true;
}
static bool registered = registerRuntime();
}  // namespace diskreport::sfc::app::algorithms::sfc
#endif