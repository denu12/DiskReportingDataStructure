#include "morton/morton.cc"
#include "app/algorithms/static/adapter.hh"
namespace diskreport::morton_Morton {
class BenchmarkMorton : public Morton {
 public:
  using Morton::Morton;
  void query(const Box& box, auto output) const {
    if (const auto* c = ::esa_campaign::active_circle) {
      const Circle circle{{c->x, c->y}, (Wide(c->radius2_hi) << 64) | c->radius2_lo};
      scan(box, [&](Point p) { return circle.contains(p); }, output);
    } else Morton::query(box, output);
  }
};
using Adapter = ::diskreport::sfc::app::algorithms::sfc::Algo<BenchmarkMorton>;
REGISTER_IMPL_NAMED(Adapter, "Morton");
}
