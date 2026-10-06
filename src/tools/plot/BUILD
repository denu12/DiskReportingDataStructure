load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library")
# py_binary(
#     name = "weight",
#     srcs = [
#         "dataloader.py",
#         "optperfprofpy.py",
#         "weight.py",
#     ],
#     deps = [
#         "//app:app_io_py_proto",  # a py_library
#         requirement("matplotlib"),
#         requirement("numpy"),
#         requirement("protobuf"),
#         requirement("pandas"),
#     ],
# )

# py_binary(
#     name = "plot",
#     srcs = [
#         "dataloader.py",
#         "optperfprofpy.py",
#         "plot.py",
#         "weight.py",
#     ],
#     deps = [
#         "//app:app_io_py_proto",  # a py_library
#         requirement("matplotlib"),
#         requirement("numpy"),
#         requirement("protobuf"),
#         requirement("pandas"),
#         requirement("scipy"),
#         requirement("jinja2"),
#         requirement("tikzplotlib"),
#     ],
# )

# py_binary(
#     name = "stats",
#     srcs = [
#         "dataloader.py",
#         "optperfprofpy.py",
#         "stats.py",
#         "weight.py",
#     ],
#     deps = [
#         "//app:app_io_py_proto",  # a py_library
#         requirement("matplotlib"),
#         requirement("numpy"),
#         requirement("protobuf"),
#         requirement("pandas"),
#         requirement("jinja2"),
#         requirement("scipy"),
#         requirement("tikzplotlib"),
#     ],
# )

# py_binary(
#     name = "to_json",
#     srcs = [
#         "to_json.py",
#     ],
#     deps = [
#         "//app:app_io_py_proto",  # a py_library
#         requirement("matplotlib"),
#         requirement("numpy"),
#         requirement("protobuf"),
#         requirement("pandas"),
#         requirement("scipy"),
#         requirement("jinja2"),
#         requirement("tikzplotlib"),
#     ],
# )

# py_binary(
#     name = "extract_exact",
#     srcs = [
#         "dataloader.py",
#         "extract_exact.py",
#     ],
#     deps = [
#         "//app:app_io_py_proto",  # a py_library
#         requirement("matplotlib"),
#         requirement("numpy"),
#         requirement("protobuf"),
#         requirement("pandas"),
#         requirement("jinja2"),
#         requirement("tikzplotlib"),
#     ],
# )

cc_library(
    name = "dataloader",
    srcs = ["dataloader.cc"],
    hdrs = ["dataloader.h"],
    deps = [
        "//app:app_io_cc_proto",
        "@abseil-cpp//absl/status:statusor",
        "@protobuf//src/google/protobuf/util:time_util",
    ],
)

load("@pybind11_bazel//:build_defs.bzl", "pybind_extension")
load("@my_deps//:requirements.bzl", "requirement")

pybind_extension(
    name = "plot_lib",
    srcs = [
        "gaussian_error.h",
        "pivot_table.h",
        "plot.cc",
        "plot.h",
    ],
    deps = [
        ":dataloader",
        "@matplotlibcpp17",
        #"@pybind11_bazel",
        # requirement("matplotlib"),
        # "@my_deps//matplotlib:pkg",
        #requirement("scikit-learn"),
        "@protobuf//src/google/protobuf/util:time_util",
        #"@spack_python",
    ],
)

py_binary(
    name = "plot_cc",
    srcs = ["plot_cc.py"],
    imports = ["."],
    deps = [
        ":plot_lib",
        requirement("matplotlib"),
        requirement("seaborn"),
        requirement("scikit-learn"),
    ],
)
