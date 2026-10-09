#include "app/algorithms/static/stann_fr.hh"
#include "app/algorithms/static/adapter.hh"
namespace diskreport::sfc::app::algorithms::sfc {
using StannFRAlgo=Algo<StannFR>;
REGISTER_IMPL_NAMED(StannFRAlgo,"stann_fr");
}
