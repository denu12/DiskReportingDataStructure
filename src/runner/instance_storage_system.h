#pragma once
#include <filesystem>

#include "absl/strings/string_view.h"
#include "app/app_io.pb.h"

namespace diskreport::runner::instance_storage_system {
namespace {
using diskreport::app::app_io::Instance;
using diskreport::app::app_io::InstanceCollection;
using diskreport::app::app_io::InstancestorageSystemConfig;

}  // namespace
class InstancestorageSystem {
 public:
  InstancestorageSystem(absl::string_view directory);
  std::vector<std::string> collection_names() const;
  std::vector<InstanceCollection> collections() const;
  void reload();
  InstancestorageSystemConfig config() const;
  size_t instance_count() const;
  std::string root_path() const;

 private:
  InstancestorageSystemConfig _config;
  std::string _directory;
  std::vector<InstanceCollection> _instance_collections;
  // TODO: add max depth?
  void find_collection(const std::filesystem::path& path);
};
}  // namespace diskreport::runner::instance_storage_system