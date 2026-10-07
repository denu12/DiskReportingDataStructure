cc_library(
    name = "sfc",
    srcs = [
        "MortonSIMD.cc",
        "MoronSIMDearly.cc",
        "esa2026.cc",
        "stann_fr.cc",
        "ann_fr.cc",
        "boost.cc",
        "cgal.cc",
        "chan_sss.cc",
        "naive.cc",
        "thst.cc",
    ],
    hdrs = [
        "esa2026.hh",
        "stann_fr.hh",
        "ann_fr.hh",
        "naive.hh",
        "chan_sss.hh",
        "sfc.hh",
    ],
    visibility = ["//visibility:public"],
    deps =
        select({
            "//:pargeo": [":sfc_pargeo"],
            "//conditions:default": [":sfc_parlay"],
        }) + [
            "//app/algorithms:algorithm_base_impl_lib",
            "//third_party/stann:stann_reporting",
            "//third_party/esa2026:nanoflann",
            "//third_party/ann:ann_euclidean",
            "//sfc",
            ":morton_scalar",
            "@CGAL",
            "@boost.foreach",
            "@boost.geometry",
            "@boost.property_map",
            "@highway//:hwy",
            "@thst",
        ],
    alwayslink = 1,
)

cc_test(
    name = "chan_sss_test",
    srcs = ["chan_sss_test.cc", "chan_sss.hh"],
    deps = ["//sfc"],
)

cc_library(
    name = "sfc_pargeo",
    srcs = [
        "pargeo.cc",
    ],
    hdrs = ["sfc.hh"],
    linkstatic = False,
    visibility = ["//visibility:public"],
    deps = [
        "//app/algorithms:algorithm_base_impl_lib",
        "//sfc",
        "@pargeo",
    ],
    alwayslink = 1,
)

cc_library(
    name = "sfc_parlay",
    srcs = [
        "pam.cc",
        "pkd_tree.cc",
    ],
    hdrs = ["sfc.hh"],
    visibility = ["//visibility:public"],
    deps = [
        "//app/algorithms:algorithm_base_impl_lib",
        "//sfc",
        "@PAM",
        "@pkd_tree",
    ],
    alwayslink = 1,
)

cc_test(
    name = "ann_fr_test",
    srcs = ["ann_fr_test.cc", "ann_fr.hh"],
    deps = ["//sfc", "//third_party/ann:ann_euclidean"],
)

cc_test(
    name = "stann_fr_test",
    srcs = ["stann_fr_test.cc", "stann_fr.hh"],
    deps = ["//sfc", "//third_party/stann:stann_reporting"],
)

cc_test(name="esa2026_test", srcs=["esa2026_test.cc","esa2026.hh"], deps=["//sfc","//third_party/esa2026:nanoflann"], linkopts=["-ldl"])

# Separate translation unit: do not auto-vectorize the scalar baseline.
cc_library(
    name = "morton_scalar",
    srcs = ["Morton.cc"],
    hdrs = ["sfc.hh"],
    copts = ["-fno-tree-vectorize", "-fno-tree-slp-vectorize"],
    deps = ["//app/algorithms:algorithm_base_impl_lib", "//sfc"],
    alwayslink = 1,
)
