#include "instance_storage_system.h"

#include <filesystem>
#include <fstream>
#include <sstream>

#include "google/protobuf/text_format.h"
#include "runner/instance_storage_system.h"

namespace diskreport::runner::instance_storage_system {
namespace {
using recursive_directory_iterator = std::filesystem::recursive_directory_iterator;
using diskreport::app::app_io::InstancestorageSystemConfig;
}  // namespace
InstancestorageSystem::InstancestorageSystem(absl::string_view directory) : _directory(directory) {
  reload();
}
InstancestorageSystemConfig InstancestorageSystem::config() const { return _config; }

std::vector<std::string> InstancestorageSystem::collection_names() const {
  std::vector<std::string> _collection_names;
  for (const auto& c : _instance_collections) {
    _collection_names.push_back(c.collection_name());
  }
  return _collection_names;
}

size_t InstancestorageSystem::instance_count() const {
  size_t count = 0;
  for (const auto& c : _instance_collections) {
    count += c.instances().size();
  }
  return count;
}

std::vector<InstanceCollection> InstancestorageSystem::collections() const {
  return _instance_collections;
}
void InstancestorageSystem::reload() {
  _instance_collections.clear();
  // look up  magic file
  std::ifstream collection_file(_directory + "/storage.textproto");
  if (!collection_file.good()) {
    std::cerr << "storage.textproto not found" << std::endl;
    exit(1);
  }
  std::stringstream buffer;
  buffer << collection_file.rdbuf();

  if (!google::protobuf::TextFormat::ParseFromString(buffer.str(), &_config)) {
    std::cerr << "Parsing error in '" << _directory + "/storage.textproto" << "'" << std::endl;
    exit(1);
  }
  for (const auto& dirEntry : recursive_directory_iterator(_directory)) {
    if (dirEntry.is_directory()) {
      find_collection(dirEntry.path());
    }
  }
}

std::string InstancestorageSystem::root_path() const { return _directory; }

void InstancestorageSystem::find_collection(const std::filesystem::path& path) {
  //  Look for collection.textproto
  std::ifstream collection_file(path.string() + "/collection.textproto");
  if (collection_file.good()) {
    // Read
    std::stringstream buffer;
    buffer << collection_file.rdbuf();
    InstanceCollection collection;
    if (!google::protobuf::TextFormat::ParseFromString(buffer.str(), &collection)) {
      std::cerr << "Parsing error in '" << path.string() + "/collection.textproto" << "'"
                << std::endl;
      exit(1);
    }

    *collection.mutable_root_path() = path.string();
    // Update file paths
    for (auto& instance : *collection.mutable_instances()) {
      *instance.mutable_file_path() = collection.root_path() + "/" + instance.file_path();
    }
    _instance_collections.push_back(collection);
  }
}
}  // namespace diskreport::runner::instance_storage_system
