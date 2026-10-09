// SPRK (IDs only): relaxed output contract, materialized IDs only.
// Upstream credit and adaptations: src/third_party/esa2026/NOTICE.txt.
#include "app/algorithms/static/esa2026.hh"
#include "benchmark/esa_campaign.hh"

namespace diskreport::sfc::app::algorithms::sfc {
namespace {
esa_campaign::Result run_sprk_ids(const esa_campaign::Dataset& data, bool verify) {
  if (!data.events.empty()) throw std::runtime_error("SPRK IDs entry is static only");
  auto& api = EsaApi::get();
  if (!api.integer_ids) throw std::runtime_error("SPRK ID bridge unavailable");
  esa_campaign::Result result;
  result.output_contract = "point_ids_only";
  auto started = std::chrono::steady_clock::now();
  std::vector<uint32_t> points;
  points.reserve(2 * data.points.size());
  for (auto p : data.points) { points.push_back(p.x); points.push_back(p.y); }
  static const uint32_t empty[2] = {};
  void* index = api.create(0, points.empty() ? empty : points.data(), data.points.size());
  struct Owner { void* index; EsaApi& api; ~Owner() { api.destroy(index); } } owner{index, api};
  result.build_seconds = esa_campaign::elapsed(started);
  auto batch_start=std::chrono::steady_clock::now();
  for (size_t i = 0; i < data.queries.size(); ++i) {
    const auto& circle = data.queries[i];
    const size_t* ids = nullptr;
    if(verify)started = std::chrono::steady_clock::now();
    // Same f32 candidates and exact integer membership as coordinate reporting;
    // this diagnostic materializes only IDs.
    const size_t count = api.integer_ids(index, circle.x, circle.y,
                                        circle.radius2_lo, circle.radius2_hi, &ids);
    result.answers += count;
    ++result.queries;
    if(verify)result.query_seconds += esa_campaign::elapsed(started);
    // Check actual IDs against the integer oracle outside query timing.
    if (verify) {
      std::vector<uint64_t> actual;
      actual.reserve(count);
      for (size_t j = 0; j < count; ++j) {
        if (ids[j] >= data.points.size()) {
          result.correct = false; result.failed_query = i; return result;
        }
        const auto p = data.points[ids[j]];
        actual.push_back(esa_campaign::key(p.x, p.y));
      }
      std::sort(actual.begin(), actual.end());
      if (actual != esa_campaign::truth(data, circle)) {
        result.correct = false; result.failed_query = i; return result;
      }
    }
  }
  if(!verify)result.query_seconds=esa_campaign::elapsed(batch_start);
 return result;
}
const bool registered = [] {
  esa_campaign::registry()["esa_sprk_CHEATING_IDS_ONLY"] = run_sprk_ids;
  return true;
}();
}  // namespace
}  // namespace diskreport::sfc::app::algorithms::sfc
