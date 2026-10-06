cc_library(
    name = "static_btree",
    hdrs = ["static_btree.hh"],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "static_btree_benchmark",
    srcs = ["static_btree_benchmark.cc"],
    visibility = ["//visibility:public"],
    deps = [
        ":static_btree",
        "@google_benchmark//:benchmark_main",
    ],
)

# The former highway_btree files are not distributed. The current Highway
# implementation and its test live in //static_btree.
