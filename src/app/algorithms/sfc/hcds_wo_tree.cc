#include <sys/types.h>

#include "app/algorithms/sfc/sfc.hh"
#include "sfc/HCDSwoTree.hpp"
namespace diskreport::sfc::app::algorithms::sfc {
using HCDSAlgoHilbert = Algo<diskreport::sfc::HCDSWOTree<u_int32_t, u_int32_t, true>>;
using HCDSAlgo = Algo<diskreport::sfc::HCDSWOTree<u_int32_t, u_int32_t, false>>;

REGISTER_IMPL_NAMED(HCDSAlgoHilbert, "hcdswot_hilbert");
REGISTER_IMPL_NAMED(HCDSAlgo, "hcdswot");

}  // namespace diskreport::sfc::app::algorithms::sfc