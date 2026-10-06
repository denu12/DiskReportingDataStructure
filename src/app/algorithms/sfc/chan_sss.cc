#include "app/algorithms/sfc/chan_sss.hh"
#include "app/algorithms/sfc/sfc.hh"
namespace diskreport::sfc::app::algorithms::sfc {
using ChanSSSAlgo = Algo<ChanSSS>;
REGISTER_IMPL_NAMED(ChanSSSAlgo, "chan_sss");
}
