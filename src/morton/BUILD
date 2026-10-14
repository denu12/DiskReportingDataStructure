cc_library(
    name = "morton",
    textual_hdrs = ["morton.cc", "mortonSIMD.cc", "morton3D.cc", "morton_d_dim.cc", "mortonplus.hpp", "mortonplus3d.hpp", "mortonplus_d_dim.hpp"],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "morton_ddim_test",
    srcs = ["morton_d_dim_test.cc"],
    deps = [":morton"],
    copts = ["-std=c++20", "-mavx2"],
)

cc_test(name="mortonplus_test", srcs=["mortonplus_test.cc"], deps=[":morton"], copts=["-std=c++20", "-mavx2", "-mbmi2"], linkopts=["-pthread"])

cc_test(name="mortonplus3d_test", srcs=["mortonplus3d_test.cc"], deps=[":morton"], copts=["-std=c++20", "-mavx2", "-mbmi2"], linkopts=["-pthread"])

cc_test(name="mortonplus_ddim_test", srcs=["mortonplus_d_dim_test.cc"], deps=[":morton"], copts=["-std=c++20", "-mavx2"])
