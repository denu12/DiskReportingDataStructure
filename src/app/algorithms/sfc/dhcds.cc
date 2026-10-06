#include "sfc/HCDS_dynamic.hpp"

//
#include <sys/types.h>

#include "app/algorithms/sfc/sfc.hh"
namespace diskreport::sfc::app::algorithms::sfc {
using DHCDSAlgdHilbert =
    Algo<diskreport::sfc::dynamic::HCDS<absl::btree_multimap, u_int32_t, u_int32_t, true>>;
using DHCDSAlgo =
    Algo<diskreport::sfc::dynamic::HCDS<absl::btree_multimap, u_int32_t, u_int32_t, false>>;

REGISTER_IMPL_NAMED(DHCDSAlgdHilbert, "dhcds_hilbert");
REGISTER_IMPL_NAMED(DHCDSAlgo, "dhcds");
// using DHCDSAlgdHilbert16 = Algo<diskreport::sfc::HCDS<u_int16_t, u_int16_t, true>>;
// using DHCDSAlgo16 = Algo<diskreport::sfc::HCDS<u_int16_t, u_int16_t, false>>;

// REGISTER_IMPL_NAMED(DHCDSAlgdHilbert16, "dhcds_hilbert16");
// REGISTER_IMPL_NAMED(DHCDSAlgo16, "dhcds16");

}  // namespace diskreport::sfc::app::algorithms::sfc