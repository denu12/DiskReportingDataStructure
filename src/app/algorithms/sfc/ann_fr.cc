#include "app/algorithms/sfc/ann_fr.hh"
#include "app/algorithms/sfc/sfc.hh"
namespace diskreport::sfc::app::algorithms::sfc {
using AnnFRAlgo = Algo<AnnFR>;
REGISTER_IMPL_NAMED(AnnFRAlgo, "ann_fr");
}
