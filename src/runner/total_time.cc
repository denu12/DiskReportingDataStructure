
#include <google/protobuf/text_format.h>
#include <google/protobuf/util/time_util.h>

#include <fstream>
#include <sstream>

#include "absl/strings/match.h"
#include "absl/strings/str_replace.h"
#include "absl/strings/substitute.h"
#include "app/app_io.pb.h"

namespace {
using diskreport::app::app_io::ExperimentConfig;
using diskreport::app::app_io::ExperimentResultMain;
using diskreport::app::app_io::ExperimentResultPart;
}  // namespace
size_t res = 0;
std::tuple<double, double, double> convert(std::ifstream& exp_file, const std::string& path) {
  ExperimentResultPart part;
  if (!part.ParseFromIstream(&exp_file)) {
    std::cout << "something went wrong " << path << std::endl;
    exit(0);
  }
  double sum = 0;
  double max = 0;
  double maxRam = 0;
  for (auto& result : part.results()) {
    if (result.run_config().short_name().find("ohc") != std::string::npos) {
      continue;
    }
    res++;
    double timespend =
        google::protobuf::util::TimeUtil::TimestampToSeconds(result.run_information().end_time()) -
        google::protobuf::util::TimeUtil::TimestampToSeconds(result.run_information().start_time());
    if (timespend > 3600) {
      std::cout << "[warn] " << timespend << " " << result.run_config().short_name() << " "
                << result.instance().name() << std::endl;
    }
    max = std::max(timespend, max);
    sum += timespend;
    maxRam = std::max(maxRam, result.run_information().max_allocated_memory_in_mb());
  }
  return {sum, max, maxRam};
}
int main(int argc, char** argv) {
  double sum = 0;
  double max = 0;
  double maxRam = 0;
  for (int i = 1; i < argc; i++) {
    std::ifstream exp_file(argv[i]);
    if (!exp_file.good()) {
      std::cerr << "The file '" << argv[i] << "' must exist." << std::endl;
      return 1;
    }
    if (absl::StrContains(argv[i], "main")) {
      std::cout << "Skipping main" << std::endl;
    } else {
      auto [sum1, max2, maxR] = convert(exp_file, argv[i]);
      sum += sum1;
      max = std::max(max2, max);
      maxRam = std::max(maxRam, maxR);
    }
  }
  std::cout << "Results: " << res << std::endl;
  std::cout << "TOTAL TIME: " << sum << " seconds" << std::endl;
  std::cout << "TOTAL TIME: " << sum / 3600.0 << " hours" << std::endl;
  std::cout << "TOTAL TIME for four: " << sum / 14400.0 << " hours" << std::endl;

  std::cout << "TOTAL MAX: " << max << " seconds" << std::endl;
  std::cout << "TOTAL MAX: " << maxRam << " MB" << std::endl;
}