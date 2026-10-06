#include <sys/types.h>

#include "app/algorithms/algorithm_impl.h"
#include "app/algorithms/sfc/sfc.hh"

#undef HWY_TARGET_INCLUDE
// For dynamic dispatch, specify the name of the current file (unfortunately
// __FILE__ is not reliable) so that foreach_target.h can re-include it.
#define HWY_TARGET_INCLUDE "app/algorithms/sfc/ehcds.cc"
// Generates code for each enabled target by re-including this source file.

#include "hwy/foreach_target.h"  // IWYU pragma: keep
#include "sfc/CEHCDS.hpp"
#include "sfc/EHCDS.hpp"
#include "static_btree/static_btree.hh"

HWY_BEFORE_NAMESPACE();
namespace diskreport::sfc::app::algorithms::sfc {
namespace HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;
template <typename DT>
using LB = ::diskreport::static_btree::HWY_NAMESPACE::ImplicitStaticBTree<DT>;
bool ERegisterAll(const std::string& suffix) {
  std::string hilbert = "ehcds_hilbert:";
  std::string normal = "ehcds:";
  std::string extra = "cehcds:";
  std::string extra_hilbert = "cehcds_hilbert:";

  std::string extra8 = "cehcds8:";

  using HCDSAlgoHilbert =
      Algo<diskreport::sfc::HWY_NAMESPACE::EHCDS<LB, u_int32_t, u_int32_t, 24, true>>;
  using HCDSAlgo = Algo<diskreport::sfc::HWY_NAMESPACE::EHCDS<LB, u_int32_t, u_int32_t, 24, false>>;
  using CHCDSAlgo =
      Algo<diskreport::sfc::HWY_NAMESPACE::CEHCDS<LB, u_int32_t, u_int32_t, 16, 24, false>>;
  using CHCDSAlgoHilbert =
      Algo<diskreport::sfc::HWY_NAMESPACE::CEHCDS<LB, u_int32_t, u_int32_t, 16, 24, true>>;
  using CHCDSAlgo8 =
      Algo<diskreport::sfc::HWY_NAMESPACE::CEHCDS<LB, u_int32_t, u_int32_t, 8, 24, false>>;
  return diskreport::app::algorithms::registerImpl<HCDSAlgoHilbert>(hilbert + suffix) &&
         diskreport::app::algorithms::registerImpl<HCDSAlgo>(normal + suffix) &&
         diskreport::app::algorithms::registerImpl<CHCDSAlgo>(extra + suffix) &&
         diskreport::app::algorithms::registerImpl<CHCDSAlgo>(extra_hilbert + suffix) &&
         diskreport::app::algorithms::registerImpl<CHCDSAlgo>(extra8 + suffix);
}
}  // namespace HWY_NAMESPACE
}  // namespace diskreport::sfc::app::algorithms::sfc
HWY_AFTER_NAMESPACE();
#if HWY_ONCE
namespace diskreport::sfc::app::algorithms::sfc {

HWY_EXPORT(ERegisterAll);
bool registerERuntime() {
  HWY_DYNAMIC_DISPATCH(ERegisterAll)("best");
  for (int64_t target : hwy::SupportedAndGeneratedTargets()) {
    hwy::SetSupportedTargetsForTest(target);
    HWY_DYNAMIC_DISPATCH(ERegisterAll)(hwy::TargetName(target));
  }
  hwy::SetSupportedTargetsForTest(0);
  return true;
}
static bool registeredE = registerERuntime();
}  // namespace diskreport::sfc::app::algorithms::sfc
#endif