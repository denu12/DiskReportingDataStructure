#pragma once
#include <filesystem>
#include <fstream>
#include <map>
#include <vector>

#include "absl/status/statusor.h"
#include "app/app_io.pb.h"
#include "google/protobuf/text_format.h"

namespace diskreport {

namespace tools {
namespace {
using diskreport::app::app_io::ExperimentResultMain;
using diskreport::app::app_io::ExperimentResultPart;
using diskreport::app::app_io::FailedExperiment;
using diskreport::app::app_io::Instance;
using diskreport::app::app_io::InstanceCollection;
using diskreport::app::app_io::Result;
using diskreport::app::app_io::Visualisation;
}  // namespace
namespace plot {
class ExperimentResult {
  std::filesystem::path path;
  ExperimentResultMain main;
  std::vector<ExperimentResultPart> vec;
  std::vector<Result> res;
  std::vector<FailedExperiment> failed_;
  std::map<std::string, Instance> replace;

  bool finished = false;

 public:
  ExperimentResult(std::filesystem::path p, bool use_correct, std::filesystem::path correct)
      : path(p) {
    if (use_correct) {
      std::cout << "[INFO] Using path: " << correct << std::endl;
      std::ifstream correct_file(correct);
      if (correct_file.good()) {
        InstanceCollection rename;
        std::stringstream string_rep;
        string_rep << correct_file.rdbuf();
        if (google::protobuf::TextFormat::ParseFromString(string_rep.str(), &rename)) {
          for (const auto& h : rename.instances()) {
            replace[h.name()] = h;
          }
          *replace["Spielman_k600_A_01.mtx"].mutable_name() = "Spielman_k600.mtx";
        } else {
          std::cout << "Failed consuming" << std::endl;
        }
      } else {
        std::cout << "[FAIL] Could not open file" << std::endl;
      }
      std::cout << "[INFO] Replacing: " << replace.size() << std::endl;
    }
  }
  bool loadMain(std::ifstream&);
  bool loadResultPart(std::ifstream&);
  absl::Status finishLoading(bool, const std::map<std::string, std::string>& rename_labels, bool,
                             bool, const std::string&);
  const std::vector<Result>& results() const { return res; }
  std::vector<FailedExperiment>& failed() { return failed_; }
  void filter(std::set<std::string> ignore_sort) {
    std::vector<Result> filtered;
    std::copy_if(res.begin(), res.end(), std::back_inserter(filtered),
                 [&](const Result& r) { return !ignore_sort.contains(r.instance().sort()); });
    if (filtered.size() != res.size()) {
      std::cout << " Successff" << std::endl;
    }
    res = filtered;
  }
};
absl::StatusOr<std::vector<ExperimentResult>> load_data(
    std::string, decltype(Visualisation().experiment_paths()) dirs,
    std::map<std::string, std::string> rename_labels, const std::string&, bool prefix_name = false,
    bool print_params = false);
}  // namespace plot
}  // namespace tools
}  // namespace diskreport