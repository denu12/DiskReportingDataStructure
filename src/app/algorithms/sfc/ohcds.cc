#include "sfc/OHCDS.hpp"

#include <sys/types.h>

#include "app/algorithms/sfc/sfc.hh"
namespace diskreport::sfc::app::algorithms::sfc {
using OHCDSAlgoHilbert = Algo<diskreport::sfc::external::HCDS<u_int32_t, u_int32_t, true>>;
using OHCDSAlgo = Algo<diskreport::sfc::external::HCDS<u_int32_t, u_int32_t, false>>;

REGISTER_IMPL_NAMED(OHCDSAlgoHilbert, "ohcds_hilbert");
REGISTER_IMPL_NAMED(OHCDSAlgo, "ohcds");
using OHCDSAlgoHilbert16 = Algo<diskreport::sfc::external::HCDS<u_int16_t, u_int16_t, true>>;
using OHCDSAlgo16 = Algo<diskreport::sfc::external::HCDS<u_int16_t, u_int16_t, false>>;

REGISTER_IMPL_NAMED(OHCDSAlgoHilbert16, "ohcds_hilbert16");
REGISTER_IMPL_NAMED(OHCDSAlgo16, "ohcds16");

}  // namespace diskreport::sfc::app::algorithms::sfc