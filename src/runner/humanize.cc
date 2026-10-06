
#include <google/protobuf/text_format.h>

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
template <class T>
void convert(std::ifstream& exp_file, const std::string& path) {
  T part;
  if (!part.ParseFromIstream(&exp_file)) {
    std::cout << "something went wrong " << path << std::endl;
    exit(0);
  }
  std::ofstream exp_fileO(absl::StrReplaceAll(path, {{"binary_proto", "textproto"}}));
  std::cout << absl::StrReplaceAll(path, {{"binary_proto", "textproto"}}) << std::endl;
  std::string result;
  google::protobuf::TextFormat::PrintToString(part, &result);
  exp_fileO << result;
}
int main(int argc, char** argv) {
  for (int i = 1; i < argc; i++) {
    std::ifstream exp_file(argv[i]);
    if (!exp_file.good()) {
      std::cerr << "The file '" << argv[i] << "' must exist." << std::endl;
      return 1;
    }
    if (absl::StrContains(argv[i], "main")) {
      convert<ExperimentResultMain>(exp_file, argv[i]);
    } else {
      convert<ExperimentResultPart>(exp_file, argv[i]);
    }
  }
}