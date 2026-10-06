
#include <sys/types.h>

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <vector>

#include "benchmark/benchmark.h"
#include "ds/static_btree.hh"
template <typename ValueType>
std::vector<ValueType> gen_data(size_t s) {
  std::vector<ValueType> points(s);
  for (auto& p : points) {
    p = rand() % (std::numeric_limits<ValueType>::max() / 40);
  }
  return points;
}

template <template <typename> typename Tree, typename ValueType>
static void TreeDirectLowerBound(benchmark::State& state) {
  srand(42);
  auto points = gen_data<ValueType>(state.range(0));
  std::sort(points.begin(), points.end());
  auto queries = gen_data<ValueType>(state.range(0) / 2);
  Tree<ValueType> tree(points);

  for (auto _ : state) {
    ValueType mask = 0;
    for (auto p : queries) {
      auto s = tree.lower_bound(p);
      auto q = std::lower_bound(points.begin(), points.end(), p);

      if ((s == std::numeric_limits<ValueType>::max() && q == points.end())) {
      } else if (q == points.end()) {
        std::cout << "ffflflf" << s << std::endl;
        throw;
      }
      if (s != *q) {
        std::cout << s << " " << *q << " " << p << std::endl;
        throw;
      }
      mask ^= s;
    }
    state.counters["mask"] = mask;
  }
}

template <template <typename> typename Tree, typename ValueType>
static void TreeLowerBound(benchmark::State& state) {
  srand(42);
  auto points = gen_data<ValueType>(state.range(0));
  std::sort(points.begin(), points.end());
  auto queries = gen_data<ValueType>(state.range(0) / 2);
  Tree<ValueType> tree(points);
  // std::cout << tree.lower_bound(0, 0) << std::endl;
  // std ::cout << tree.lower_bound(3, 0) << std::endl;
  // std::cout << tree.lower_bound(0, 5) << std::endl;

  // std::cout << tree.N << " " << tree.S << " " << tree.T << std::endl;
  for (auto _ : state) {
    ValueType mask = 0;
    for (auto p : queries) {
      // std::cout << p << std::endl;
      auto s2 = tree.lower_bound2(p);
      // auto s = points.begin() + s2;
      //  auto q = std::upper_bound(points.begin(), points.end(), p);

      // if (s != q) {
      //   std::cout << *s << " " << *q << " " << p << std::endl;
      //   throw;
      // }
      mask ^= s2;
    }
    state.counters["mask"] = mask;
  }
}
template <typename ValueType>
static void StdLowerBound(benchmark::State& state) {
  srand(42);
  auto points = gen_data<ValueType>(state.range(0));
  std::sort(points.begin(), points.end());
  auto queries = gen_data<ValueType>(state.range(0));
  for (auto _ : state) {
    ValueType mask = 0;
    for (auto p : queries) {
      auto q = std::lower_bound(points.begin(), points.end(), p);
      //   if ((s == std::numeric_limits<ValueType>::max() && q == points.end())) {
      //   } else if (s != *q) {
      //     std::cout << s << " " << *q << " " << p << std::endl;
      //     throw;
      //   }
      mask ^= (q == points.end() ? std::numeric_limits<ValueType>::max() : *q);
    }
    state.counters["mask"] = mask;
  }
}

/*BENCHMARK(TreeLowerBound<StaticBTree, int>)
    ->Arg(100)
    ->Arg(1000)
    ->Arg(10000)
    ->Arg(1e6)
    ->Arg(1e7)
    ->Arg(1e8);
BENCHMARK(TreeLowerBound<ImplicitStaticBPlusTree, int>)
    ->Arg(100)
    ->Arg(1000)
    ->Arg(10000)
    ->Arg(1e6)
    ->Arg(1e7)
    ->Arg(1e8);
BENCHMARK(StdLowerBound<int>)->Arg(100)->Arg(1000)->Arg(10000)->Arg(1e6)->Arg(1e7)->Arg(1e8);*/
BENCHMARK(TreeLowerBound<ImplicitStaticBPlusTree, uint64_t>)
    ->Arg(100)
    ->Arg(1000)
    ->Arg(10000)
    ->Arg(1e6)
    ->Arg(1e7)
    ->Arg(1e8);
// BENCHMARK(StdLowerBound<uint64_t>)->Arg(100)->Arg(1000)->Arg(10000)->Arg(1e6)->Arg(1e7)->Arg(1e8);
