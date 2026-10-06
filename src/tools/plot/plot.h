#pragma once

#include <algorithm>
#include <any>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "Python.h"
#include "absl/status/status.h"
#include "app/app_io.pb.h"
#include "dataloader.h"
#include "matplotlibcpp17/pyplot.h"
#include "src/google/protobuf/util/time_util.h"
#include "tools/plot/gaussian_error.h"
#include "tools/plot/pivot_table.h"

namespace diskreport {
namespace tools {
namespace plot {

namespace {
using diskreport::app::app_io::FailedExperiment;
using diskreport::app::app_io::Result;
using diskreport::app::app_io::Visualisation;
using diskreport::app::app_io::VisualisationsFile;
}  // namespace
template <typename T>
struct GroupByEvaluator {
  std::function<T(T)> unary_operator;
  std::function<T(T, T)> binary_operator;
  std::function<T(T, size_t, std::vector<T>&)> final;
  T start_value = T{};
  GroupByEvaluator() {}
  GroupByEvaluator(std::function<T(T)> u, std::function<T(T, T)> b,
                   std::function<T(T, size_t, std::vector<T>&)> f, T s = T{})
      : unary_operator(u), binary_operator(b), final(f), start_value(s) {}
  GroupByEvaluator(const GroupByEvaluator&) = default;
  GroupByEvaluator(GroupByEvaluator&&) = default;
  GroupByEvaluator& operator=(const GroupByEvaluator&) = default;
  GroupByEvaluator& operator=(GroupByEvaluator&&) = default;
};
template <typename T>
GroupByEvaluator<T> MaxEvaluator() {
  return GroupByEvaluator<T>([](T a) { return a; }, [](T a, T b) { return std::max(a, b); },
                             [](T a, size_t, std::vector<T>&) { return a; }, T((int64_t)0));
}
template <typename T>
auto MinEvaluator() {
  return GroupByEvaluator<T>([](T a) { return a; }, [](T a, T b) { return a < b ? a : b; },
                             [](T a, size_t, std::vector<T>&) { return a; },
                             T(std::numeric_limits<int64_t>::max()));
}
template <typename T>
auto FailEvaluator() {
  return GroupByEvaluator<T>([](T a) { return a; }, [](T a, T b) { return b; },
                             [](T a, size_t n, std::vector<T>&) { return a; }, T{});
};
template <typename T>
auto AvgEvaluator() {  // TODO() Add support for stddev

  return GroupByEvaluator<T>([](T a) { return a; }, [](T a, T b) { return a + b; },
                             [](T a, size_t n, std::vector<T>& data) {
                               double avg_ = a.to_double() / ((double)n);
                               auto curried_avg = [avg_](T x) -> double {
                                 double diff = (x.to_double() - avg_);
                                 return diff * diff;
                               };

                               // Calculate sum of squared differences
                               double sum_of_squares = std::transform_reduce(
                                   data.begin(), data.end(), 0.0, std::plus<>(), curried_avg);
                               // Apply Bessel's correction (n - 1)
                               // Note: Add a safety check if n <= 1 to avoid division by zero!
                               double variance = (n > 1) ? (sum_of_squares / (n - 1)) : 0.0;

                               return GaussianError<double>(avg_, std::sqrt(variance));
                             },
                             T(0.0f));
};
template <typename T>
auto GeomeanLogEvaluator() {
  return GroupByEvaluator<T>(
      [](T a) -> T { return log(a.to_double()); }, [](T a, T b) { return a + b; },
      [](T a, size_t n, std::vector<T>&) { return exp(a.to_double() / ((double)n)); }, T(0.0f));
};
template <typename D, typename GroupType>
class GroupBy {
  using Predicate = std::function<GroupType(D)>;
  using HavingPredicate = std::function<bool(GroupType, const std::vector<D>&)>;
  using WherePredicate = std::function<bool(const D&)>;

  template <typename A, typename B>
  using MapType = std::map<A, B>;
  MapType<GroupType, std::vector<D>> by_group;
  GroupBy(const MapType<GroupType, std::vector<D>>& dat) : by_group(dat) {}

 public:
  GroupBy(const std::vector<D>& data, Predicate by) {
    for (auto& d : data) {
      by_group[by(d)].push_back(d);
    }
  }
  template <class C>
  GroupBy(const C& container, Predicate by) {
    for (auto elem : container) {
      by_group[by(elem)].push_back(elem);
    }
  }
  size_t max_count() {
    return std::max_element(by_group.begin(), by_group.end(),
                            [](auto a, auto b) { return a.second.size() < b.second.size(); })
        ->second.size();
  }
  MapType<GroupType, size_t> count() {
    MapType<GroupType, size_t> result;
    for (const auto& [k, v] : by_group) {
      result[k] = v.size();
    }
    return result;
  }
  template <class C>
  std::vector<C> transform(GroupType t, std::function<C(D)> op) {
    std::vector<C> result;
    std::transform(by_group[t].begin(), by_group[t].end(), std::back_inserter(result), op);
    return result;
  }
  template <class C>
  std::map<GroupType, std::vector<C>> transform_all(std::function<C(D)> op) {
    std::map<GroupType, std::vector<C>> result;
    for (auto k : keys()) {
      result[k] = transform(k, op);
    }
    return result;
  }

  size_t min_count() {
    return std::min_element(by_group.begin(), by_group.end(),
                            [](auto a, auto b) { return a.second.size() < b.second.size(); })
        ->second.size();
  }
  GroupBy having(HavingPredicate pred) {
    MapType<GroupType, std::vector<D>> data;
    for (const auto& [k, v] : by_group) {
      if (pred(k, v)) {
        std::copy(v.begin(), v.end(), std::back_inserter(data[k]));
      }
    }
    return GroupBy(data);
  }
  GroupBy where(WherePredicate pred) {
    MapType<GroupType, std::vector<D>> data;
    for (const auto& [k, v] : by_group) {
      std::copy_if(v.begin(), v.end(), std::back_inserter(data[k]), pred);
      std::cout << k << ": " << data[k].size() << std::endl;
    }
    return GroupBy(data);
  }
  template <typename T>
  MapType<GroupType, T> agg(
      std::function<T(D)> access, std::function<T(T, T)> func,
      std::function<T(T, size_t)> final = [](T a) { return a; }, T start_value = T{}) {
    MapType<GroupType, T> result;
    for (auto& [gr, data_points] : by_group) {
      result[gr] = final(
          std::transform_reduce(data_points.begin(), data_points.end(), start_value, func, access),
          data_points.size());
    }
    return result;
  }
  template <typename T>
  MapType<GroupType, T> agg_final(
      std::function<T(D)> access, std::function<T(T, T)> func,
      std::function<T(T, size_t, std::vector<T>&)> final = [](T a) { return a; },
      T start_value = T{}) {
    MapType<GroupType, T> result;
    for (auto& [gr, data_points] : by_group) {
      std::vector<T> transformed(data_points.size());
      std::transform(data_points.begin(), data_points.end(), transformed.begin(), access);
      result[gr] = final(
          std::transform_reduce(data_points.begin(), data_points.end(), start_value, func, access),
          data_points.size(), transformed);
    }
    return result;
  }
  template <typename T>
  MapType<std::array<GroupType, 2>, T> agg_many(
      const std::set<GroupType>& elements, std::function<T(D, const GroupType&)> access,
      MapType<GroupType, GroupByEvaluator<T>> evaluators) {
    MapType<std::array<GroupType, 2>, T> result;
    std::cout << "size: " << elements.size() << std::endl;
    for (const auto& elem : elements) {
      std::function<T(D)> acc = [&](D d) -> T {
        return evaluators.at(elem).unary_operator(access(d, elem));
      };
      auto elems = agg_final(acc, evaluators.at(elem).binary_operator, evaluators.at(elem).final,
                             evaluators.at(elem).start_value);
      for (auto [k, v] : elem) {
        std::cout << "elem " << k << " " << v.to_string() << std::endl;
      }
      for (auto [k, v] : elems) {
        result[{k, elem}] = v;
      }
    }
    return result;
  }
  template <typename T, typename AccType = GroupType>
  auto agg_multi(const std::set<AccType>& elements, std::function<T(D, const AccType&)> access,
                 MapType<AccType, GroupByEvaluator<T>> evaluators) {
    MapType<GroupType, MapType<AccType, T>> result;
    std::cout << "size: " << elements.size() << std::endl;
    for (const auto& elem : elements) {
      std::function<T(D)> acc = [&](D d) -> T {
        return evaluators.at(elem).unary_operator(access(d, elem));
      };
      auto elems = agg_final(acc, evaluators.at(elem).binary_operator, evaluators.at(elem).final,
                             evaluators.at(elem).start_value);

      for (auto [k, v] : elems) {
        result[k][elem] = v;
      }
    }
    return result;
  }
  template <typename T = double>
  MapType<GroupType, T> geo_mean_log(std::function<T(D)> access) {
    return agg<T>(
        [&](D a) -> T {
          if (access(a) <= 0.0) {
            std::cout << "WARN zero " << access(a) << std::endl;
          }
          if (!std::isfinite(access(a))) {
            std::cout << "NAN " << access(a) << std::endl;
          }
          return log(access(a));
        },
        [](T a, T b) {
          if (!std::isfinite(a)) {
            std::cout << "aNAN " << a << std::endl;
          }
          if (!std::isfinite(b)) {
            std::cout << "bNAN " << b << std::endl;
          }
          return a + b;
        },
        [](T a, size_t n) {
          std::cout << a << " " << n << std::endl;
          return exp(a / ((T)n));
        },
        0);
  }
  template <typename T = double>
  MapType<GroupType, GaussianError<T>> avg(std::function<T(D)> access) {
    auto avg_ =
        agg<T>(access, [](T a, T b) { return a + b; }, [](T a, size_t n) { return a / ((T)n); });

    MapType<GroupType, GaussianError<T>> result;
    for (auto& [gr, data_points] : by_group) {
      std::function<T(D)> curried_avg = [&](auto a) {
        return (access(a) - avg_[gr]) * (access(a) - avg_[gr]);
      };
      result[gr] = GaussianError<T>(
          avg_[gr], std::sqrt(std::transform_reduce(
                                  data_points.begin(), data_points.end(), T{0},
                                  [](auto a, auto b) { return a + b; }, curried_avg) /
                              data_points.size()));
    }
    return result;
  }
  auto keys() {
    std::set<GroupType> result;
    for (const auto& [k, v] : by_group) {
      result.insert(k);
    }
    return result;
  }
  template <typename T = double>
  MapType<GroupType, T> min(std::function<T(D)> access) {
    return agg<T>(
        access, [](T a, T b) { return std::min(a, b); }, [](T a, size_t n) { return a; },
        std::numeric_limits<T>::max());
  }
  template <typename T = double>
  MapType<GroupType, T> max(std::function<T(D)> access) {
    return agg<T>(
        access, [](T a, T b) { return std::max(a, b); }, [](T a, size_t n) { return a; }, T{0});
  }
  auto different_element_count() const { return by_group.size(); }
};

template <typename D, typename GroupType>
class FilterBy {
  using Predicate = std::function<GroupType(D)>;
  template <typename A, typename B>
  using MapType = std::map<A, B>;
  MapType<GroupType, std::vector<D>> by_group;

 public:
  template <class Container>
  FilterBy(const Container& data, Predicate by) {
    for (auto& d : data) {
      by_group[by(d)].push_back(d);
    }
  }
  std::vector<D> at_least_one(std::function<bool(D)> pred) const {
    std::vector<D> result;
    for (const auto& [gr, gr_data] : by_group) {
      if (std::any_of(gr_data.begin(), gr_data.end(), pred)) {
        std::copy(gr_data.begin(), gr_data.end(), std::back_inserter(result));
      }
    }
    return result;
  }
  std::vector<D> all(std::function<bool(D)> pred) const {
    std::vector<D> result;
    for (const auto& [gr, gr_data] : by_group) {
      if (std::all_of(gr_data.begin(), gr_data.end(), pred)) {
        std::copy(gr_data.begin(), gr_data.end(), std::back_inserter(result));
      }
    }
    return result;
  }
};

class VisualisationTool {
  pybind11::module_ mod, seaborn, pandas;
  matplotlibcpp17::pyplot::PyPlot plt;
  VisualisationsFile file;
  void ensurePathsExists(std::string, Visualisation& vis);
  absl::Status plot_performance_profile_internal(Visualisation vis, std::vector<Result>& data,
                                                 std::string sort = "all", int cap = 0);
  std::map<std::string, std::vector<Result>> transform_by_sort(std::vector<ExperimentResult>& data,
                                                               Visualisation vis);
  std::map<std::string, std::vector<FailedExperiment>> transform_by_sort_failed(
      std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status scatter_plot_internal(Visualisation vis, std::vector<Result>& data,
                                     std::string sort = "all", int cap = 0);
  absl::Status table_internal(Visualisation vis, std::vector<Result>& data,
                              std::vector<FailedExperiment>& failed,
                              const std::set<std::string> index, const std::set<std::string> pivot,
                              std::string sort = "all", int64_t cap = 0);
  absl::Status stats_table_internal(Visualisation vis, std::vector<Result>& data,
                                    std::vector<FailedExperiment>& failed,
                                    const std::set<std::string> index,
                                    const std::set<std::string> pivot, std::string sort = "all",
                                    int64_t cap = 0);
  absl::Status stats_internal(Visualisation vis, std::vector<Result>& data,
                              std::vector<FailedExperiment>& failed, std::string sort = "all",
                              int cap = 0);
  absl::Status table(std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status categorial_bar_plot_internal(Visualisation vis, std::vector<Result>& data,
                                            std::vector<FailedExperiment>& failed,
                                            std::string sort = "all", int cap = 0);
  absl::Status categorial_bar_plot(std::vector<ExperimentResult>& data, Visualisation vis);

  absl::Status violin_plot_internal(Visualisation vis, std::vector<Result>& data,
                                    std::vector<FailedExperiment>& failed, std::string sort = "all",
                                    int cap = 0);
  absl::Status scaling_plot_internal(Visualisation vis, std::vector<Result>& data,
                                     std::vector<FailedExperiment>& failed,
                                     std::string sort = "all", int cap = 0);
  absl::Status write_csv_internal(Visualisation vis, std::vector<Result>& data,
                                  std::vector<FailedExperiment>& failed, std::string sort = "all",
                                  int cap = 0);
  absl::Status robustness_plot_internal(Visualisation vis, std::vector<Result>& data,
                                        std::vector<FailedExperiment>& failed,
                                        std::string sort = "all", int cap = 0);
  absl::Status violin_plot(std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status scaling_plot(std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status stats_table(std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status stats(std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status write_csv(std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status efficency(std::vector<ExperimentResult>& data, Visualisation vis);
  absl::Status robustness_plot(std::vector<ExperimentResult>& data, Visualisation vis);

  absl::Status efficency_internal(matplotlibcpp17::figure::Figure& fig,
                                  matplotlibcpp17::axes::Axes& ax, Visualisation vis,
                                  std::vector<Result>& data, std::string sort = "all", int cap = 0);
  absl::Status plot_internal(
      std::vector<ExperimentResult>& data, Visualisation vis,
      std::function<absl::Status(Visualisation, std::vector<Result>&, std::string, int)> function);
  const std::map<std::string, std::function<Any(Result)>> performance_characteristics = {
      {"first_debug_average_d",
       [](Result r) -> Any {
         return r.algorithm_run_informations()[0].debug_information().double_info().at("average_d");
       }},
      {"first_debug_max_d",
       [](Result r) -> Any {
         return r.algorithm_run_informations()[0].debug_information().int64_info().at("max_d");
       }},
      {"first_debug_m",
       [](Result r) -> Any {
         return r.algorithm_run_informations()[0].debug_information().int64_info().at("m");
       }},
      {"first_debug_n",
       [](Result r) -> Any {
         return r.algorithm_run_informations()[0].debug_information().int64_info().at("n");
       }},
      {"first_debug_max_node_degree",
       [](Result r) -> Any {
         return r.algorithm_run_informations()[0].debug_information().int64_info().at(
             "max_node_degree");
       }},
      {"last_edge_count",
       [](Result r) -> Any {
         return r.algorithm_run_informations()[r.algorithm_run_informations_size() - 1]
             .edge_count();
       }},
      {"runtime",
       [](Result D) -> Any {
         return GaussianError<double>(::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                                          D.run_information().algo_duration()) /
                                      1.0e9);
       }},
      {"query_duration",
       [](Result D) -> Any {
         return GaussianError<double>(::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                                          D.run_information().query_duration()) /
                                      1.0e9);
       }},
      {"query_duration_bycount",
       [](Result D) -> Any {
         return GaussianError<double>(::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                                          D.run_information().query_duration()) /
                                      1.0e9) /
                ((double)D.instance().insertion_count());
       }},
      {"construction_duration0",
       [](Result D) -> Any {
         return GaussianError<double>(
             ::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                 D.algorithm_run_informations()[0].construction_duration()) /
             1.0e9);
       }},
      {"construction_duration0_bycount",
       [](Result D) -> Any {
         return GaussianError<double>(
                    ::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                        D.algorithm_run_informations()[0].construction_duration()) /
                    1.0e9) /
                ((double)D.instance().insertion_count());
       }},
      {"true_query_duration",
       [](Result D) -> Any {
         return GaussianError<double>(::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                                          D.run_information().true_duration()) /
                                      1.0e9);
       }},
      {"true_query_count",
       [](Result D) -> Any {
         auto res = D.algorithm_run_informations().at(0).true_queries_stat();
         return res.count();
       }},
      {"query_mean",
       [](Result D) -> Any {
         auto res = D.algorithm_run_informations().at(0).queries_stat();
         return GaussianError<double>(res.mean(), res.stddev());
       }},
      {"true_query_mean",
       [](Result D) -> Any {
         auto res = D.algorithm_run_informations().at(0).true_queries_stat();
         return GaussianError<double>(res.mean(), res.stddev());
       }},
      {"deletion_mean",
       [](Result D) -> Any {
         auto res = D.algorithm_run_informations().at(0).deletion_stat();
         return GaussianError<double>(res.mean(), res.stddev());
       }},
      {"insertions_mean",
       [](Result D) -> Any {
         auto res = D.algorithm_run_informations().at(0).insertions_stat();
         return GaussianError<double>(res.mean(), res.stddev());
       }},
      {"insertion_duration",
       [](Result D) -> Any {
         return GaussianError<double>(::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                                          D.run_information().insertion_duration()) /
                                      1.0e9);
       }},
      {"runInformation_"
       "algoDuration",
       [](Result D) -> Any {
         return GaussianError<double>(::google::protobuf::util::TimeUtil::DurationToNanoseconds(
                                          D.run_information().algo_duration()) /
                                      1.0e9);
       }},

      {"memory_bycount",
       [](Result D) -> Any {
         return D.run_information().max_allocated_memory_in_mb() / D.instance().insertion_count();
       }},

      {"memory", [](Result D) -> Any { return D.run_information().max_allocated_memory_in_mb(); }},
      {"size", [](Result D) -> Any { return D.size(); }},
      {"runConfig_"
       "shortName",
       [](Result D) { return D.run_config().short_name(); }},
      {"construct_dist", [](Result D) { return D.instance().construct_dist(); }},
      {"fixed_w", [](Result D) { return D.instance().double_params().at("fixed_w"); }},
      {"instance_name_"
       "sort",
       [](Result D) { return D.instance().sort(); }},

      {"instance_query_distribution", [](Result D) { return D.instance().query_dist(); }},

      {"instance_name", [](Result D) { return D.instance().name(); }},
      {"instance_ninsert", [](Result D) { return (D.instance().insertion_count()); }},
      {"instance_ninsert_log10",
       [](Result D) {
         return "$10^{" + std::to_string(std::ceil(log10(D.instance().insertion_count()))) + "}$";
       }},

      {"instance_nquery_to_inserts",
       [](Result D) -> Any {
         return float(D.instance().query_count()) / float(D.instance().insertion_count());
       }},

      {"instance_doublew", [](Result D) { return (D.instance().double_params().at("fixed_w")); }},

      {"instance_format", [](Result D) { return (D.instance().format()); }},

      {"instance_seed", [](Result D) { return (D.instance().seed()); }},
      {"instance_nquery", [](Result D) { return (D.instance().query_count()); }},
      {"instance_name_insert_type", [](Result D) { return D.instance().insert_type(); }}};
  const std::map<std::string, std::function<Any(FailedExperiment)>>
      performance_characteristics_failed = {
          {"instance_query_distribution",
           [](FailedExperiment D) { return D.instance().query_dist(); }},
          {"instance_nquery_to_inserts",
           [](FailedExperiment D) -> Any {
             return float(D.instance().query_count()) / float(D.instance().insertion_count());
           }},
          {"instance_seed", [](FailedExperiment D) { return (D.instance().seed()); }},

          {"query_duration", [](FailedExperiment D) -> Any { return Any(); }},
          {"construction_duration0", [](FailedExperiment D) -> Any { return Any(); }},

          {"runtime", [](FailedExperiment D) -> Any { return Any(D.reason()); }},
          {"runInformation_algoDuration", [](FailedExperiment D) -> Any { return Any(); }},
          {"m/n", [](FailedExperiment D) { return Any(); }},
          {"instance_ninsert", [](FailedExperiment D) { return (D.instance().insertion_count()); }},
          {"instance_nquery", [](FailedExperiment D) { return (D.instance().query_count()); }},
          {"size", [](FailedExperiment D) { return Any(); }},
          {"weight", [](FailedExperiment D) { return Any(); }},

          {"runConfig_shortName", [](FailedExperiment D) { return D.run_config().short_name(); }},
          {"instance_name", [](FailedExperiment D) { return D.instance().name(); }},
          {"instance_ninsert", [](FailedExperiment D) { return (D.instance().insertion_count()); }},
          {"instance_doublew",
           [](FailedExperiment D) { return (D.instance().double_params().at("fixed_w")); }},

          {"instance_name_sort", [](FailedExperiment D) { return D.instance().sort(); }},
          {"instance_format", [](FailedExperiment D) { return D.instance().sort(); }},
          {"instance_name_insert_type",
           [](FailedExperiment D) { return D.instance().insert_type(); }}};
  std::map<std::string, std::pair<std::string, int>> color_line_map;
  std::vector<std::string> styles = {"-", "--", "-.", ":"};
  std::vector<std::string> markers = {
      ".", "o", "v", "^", "<", ">", "8", "s", "p", "*",
  };

 public:
  VisualisationTool(const std::string& vis_file);
  absl::Status plot(std::string root_path);
};

}  // namespace plot
}  // namespace tools
};  // namespace diskreport