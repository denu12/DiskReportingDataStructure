load("@protobuf//bazel:cc_proto_library.bzl", "cc_proto_library")
load("@rules_cc//cc:defs.bzl", "cc_binary")
load("@rules_proto//proto:defs.bzl", "proto_library")

cc_binary(
    name = "app",
    srcs = [
        "app.cc",
        "//:build-info.h",
    ],
    malloc = select({
        "//:gperftools_tcmalloc": "@gperftools",
        "//conditions:default": "@bazel_tools//tools/cpp:malloc",
    }),
    deps = [
        ":app_io_cc_proto",
        "//app/algorithms/dynamic/sfc",
        "//app/algorithms/sfc",
        "//utils:logging",
        "//utils:random_lib",
        "@abseil-cpp//absl/flags:flag",
        "@abseil-cpp//absl/flags:parse",
        "@abseil-cpp//absl/status:statusor",
    ],
)

cc_proto_library(
    name = "app_io_cc_proto",
    visibility = ["//visibility:public"],
    deps = [":app_io_proto"],
)

proto_library(
    name = "app_io_proto",
    srcs = ["app_io.proto"],
    deps = [
        "@protobuf//:duration_proto",
        "@protobuf//:timestamp_proto",
    ],
)

# verifier.cc is not part of the distributed source archive.

cc_binary(name="esa_runner",srcs=["esa_runner.cc"],deps=["//sfc","//app/algorithms/sfc","//app/algorithms/dynamic/sfc"],linkopts=["-ldl"])
