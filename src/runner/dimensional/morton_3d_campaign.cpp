#include "../../morton/morton3D.cc"
#include <iterator>
#include <fstream>
#include <iostream>
#include <string>
#include <chrono>
bool benchmark_mode=false;

template<class T> T read(std::istream& in) {
  T value{};
  if (!in.read(reinterpret_cast<char*>(&value), sizeof(value)))
    throw std::runtime_error("Truncated campaign input");
  return value;
}
template<std::size_t D> int run(std::istream& in) {
  using I = diskreport::morton3d::Morton3D;
  using P = typename I::Point;
  using W = unsigned __int128;
  auto n = read<std::uint64_t>(in), q = read<std::uint64_t>(in);
  std::vector<P> points(n);
  for (auto& p : points) for (auto& x : p) x = read<std::uint32_t>(in);
  const auto build_start=std::chrono::steady_clock::now();
  I index(points);
  const double build_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-build_start).count();
  double query_seconds=0;
  std::size_t answers = 0;
  std::vector<P> actual;
  for (std::size_t j = 0; j < q; ++j) {
    P center{};
    for (auto& x : center) x = read<std::uint32_t>(in);
    W radius2 = read<std::uint64_t>(in);
    radius2 |= W(read<std::uint64_t>(in)) << 64;
    actual.clear();
    std::vector<P> expected;
    const auto query_start=std::chrono::steady_clock::now();
    index.query_squared(center, radius2, std::back_inserter(actual));
    query_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-query_start).count();
    answers += actual.size();
    if (benchmark_mode) continue;
    // Independent full scan, accumulating rather than subtracting distances.
    for (std::size_t i = 0; i < n; ++i) {
      W distance = 0;
      for (std::size_t a = 0; a < D; ++a) {
        auto delta = std::int64_t(points[i][a]) - center[a];
        auto mag = std::uint64_t(delta < 0 ? -delta : delta);
        distance += W(mag) * mag;
      }
      if (distance <= radius2) expected.push_back(points[i]);
    }
    std::sort(actual.begin(), actual.end());
    std::sort(expected.begin(), expected.end());
    if (actual != expected) {
      std::cout << "{\"status\":\"incorrect\",\"query\":" << j << "}\n";
      return 2;
    }
  }
  std::cout << "{\"status\":\"success\",\"points\":" << n
            << ",\"queries\":" << q << ",\"answers\":" << answers
            << ",\"build_seconds\":" << build_seconds << ",\"query_seconds\":" << query_seconds << "}\n";
  return 0;
}
int main(int argc, char** argv) {
  try {
    if (argc < 2 || argc > 4) throw std::runtime_error("Usage: morton_3d_check CASE.bin [ALGORITHM] [--bench]");
    benchmark_mode=argc==4 && std::string(argv[3])=="--bench";
    const std::string algorithm = argc >= 3 ? argv[2] : "Morton3D";
    if (algorithm != "Morton3D") throw std::runtime_error("Unknown algorithm");
    std::ifstream in(argv[1], std::ios::binary);
    auto d = read<std::uint32_t>(in);
    switch (d) {
#define DIM(N) case N: return run<N>(in);
      DIM(3)
#undef DIM
      default: throw std::runtime_error("Unsupported campaign dimension");
    }
  } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
