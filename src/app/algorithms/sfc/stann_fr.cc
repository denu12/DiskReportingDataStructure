#include "app/algorithms/sfc/stann_fr.hh"
#include "app/algorithms/sfc/sfc.hh"
namespace diskreport::sfc::app::algorithms::sfc {
using StannFRAlgo=Algo<StannFR>;
REGISTER_IMPL_NAMED(StannFRAlgo,"stann_fr");
}
