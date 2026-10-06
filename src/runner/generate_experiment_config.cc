#include <google/protobuf/text_format.h>

#include <fstream>

#include "absl/algorithm/container.h"
#include "absl/flags/flag.h"
#include "absl/flags/parse.h"
#include "absl/flags/usage.h"
#include "absl/strings/match.h"
#include "absl/strings/str_replace.h"
#include "absl/strings/substitute.h"
#include "app/app_io.pb.h"
#include "runner/instance_storage_system.h"

namespace {
using diskreport::app::app_io::ExperimentConfig;
using diskreport::app::app_io::Instance;
using diskreport::app::app_io::instanceFilter;
using diskreport::runner::instance_storage_system::InstancestorageSystem;
}  // namespace

ABSL_FLAG(std::string, experiment_path, "", "The path to the folder including definitions file.");
ABSL_FLAG(std::string, instance_filter, "",
          "instanceFilter textproto. Note that if sort,*_weight_types, or "
          "format is empty "
          "all are accepted.");
ABSL_FLAG(std::string, data_path, "",
          "Path to the data file for instances following the structure");
ABSL_FLAG(std::string, run_configs, "", "Run config object as textproto.");
ABSL_FLAG(std::string, experiment_name, "", "Experiment name");
ABSL_FLAG(bool, exclusive, false, "Is this process exclusive");
ABSL_FLAG(int, concurrent_processes, 1, "How many task are run at the same time.");
ABSL_FLAG(int, repetitions, 1, "How many repetitions of this experiment.");
ABSL_FLAG(int, sample, -1, "How many instances should be used.");
ABSL_FLAG(std::string, sample_by, "m/n",
          "Which sample method should be used uniform sampling based on m/n");

int main(int argc, char** argv) {
  absl::SetProgramUsageMessage("Builds a experiment.textproto");
  absl::ParseCommandLine(argc, argv);

  std::string exp_path = absl::GetFlag(FLAGS_experiment_path);
  std::string exp_name = absl::GetFlag(FLAGS_experiment_name);
  std::string run_configs = absl::GetFlag(FLAGS_run_configs);
  std::string data_path = absl::GetFlag(FLAGS_data_path);
  std::string instance_filter_s = absl::GetFlag(FLAGS_instance_filter);

  bool exclusive = absl::GetFlag(FLAGS_exclusive);
  ExperimentConfig experiment_config;
  ExperimentConfig experiment_config2;
  instanceFilter instance_filter;
  if (!google::protobuf::TextFormat::ParseFromString(instance_filter_s, &instance_filter)) {
    std::cerr << "Error parsing 'instance_filter'." << std::endl;
    return 1;
  }
  // max edges/nodes can be ommitted
  instance_filter.set_max_edges(instance_filter.max_edges() == 0
                                    ? std::numeric_limits<int64_t>::max()
                                    : instance_filter.max_edges());
  // TODO leonie filter
  instance_filter.set_max_nodes(instance_filter.max_nodes() == 0
                                    ? std::numeric_limits<int64_t>::max()
                                    : instance_filter.max_nodes());
  *experiment_config.mutable_filter() = instance_filter;

  experiment_config.set_repetitions(absl::GetFlag(FLAGS_repetitions));

  if (!google::protobuf::TextFormat::ParseFromString(run_configs, &experiment_config2)) {
    std::cerr << "Error parsing 'run_configs'." << std::endl;
    return 1;
  }

  *experiment_config.mutable_experiment_name() = exp_name;
  *experiment_config.mutable_run_configs() = experiment_config2.run_configs();
  experiment_config.set_exclusive(exclusive);

  InstancestorageSystem hyper_storage_system(data_path);
  *experiment_config.mutable_root_path() = hyper_storage_system.root_path();
  for (const auto& name : hyper_storage_system.collection_names()) {
    std::cout << name << std::endl;
  }
  std::cout << "Found " << hyper_storage_system.collection_names().size()
            << " collections containing " << hyper_storage_system.instance_count()
            << " instances. Processing." << std::endl;

  std::vector<Instance> instances;
  for (auto& collection : hyper_storage_system.collections()) {
    if (absl::c_any_of(
            instance_filter.instance_collections(),
            [&collection](auto a) { return a.name() == collection.collection_name(); }) ||
        instance_filter.instance_collections().empty()) {
      for (auto& instance : *collection.mutable_instances()) {
        // TODO leonie filter
        if (instance.insertion_count() <= instance_filter.max_edges() &&
            instance.insertion_count() >= instance_filter.min_edges() &&
            instance.query_count() <= instance_filter.max_nodes() &&
            instance.query_count() >= instance_filter.min_nodes() &&
            (absl::c_any_of(instance_filter.sorts(),
                            [&instance](auto a) { return a == instance.sort(); }) ||
             instance_filter.sorts().empty()) &&
            (absl::c_any_of(instance_filter.collections(),
                            [&instance](auto a) { return a == instance.collection(); }) ||
             instance_filter.collections().empty()) &&
            (instance_filter.format() == instance.format() || instance_filter.format().empty())) {
          // adjust path to root directory
          std::string f_path(
              absl::StrReplaceAll(instance.file_path(), {{hyper_storage_system.root_path(), ""}}));
          *(instance.mutable_file_path()) = f_path;
          instances.push_back(instance);
        }
      }
    }
  }

  std::cout << "Found " << instances.size() << " instances for this experiment." << std::endl;

  *experiment_config.mutable_instances() = {instances.begin(), instances.end()};
  experiment_config.set_concurrent_processes(absl::GetFlag(FLAGS_concurrent_processes));
  std::ofstream exp_file(exp_path + "/experiment.textproto");
  std::string result;
  google::protobuf::TextFormat::PrintToString(experiment_config, &result);
  exp_file << result;
}