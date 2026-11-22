"""Pinned Indexicon range-reporting variants and campaign capabilities."""
REVISION = '69da8a364f3437a1110d89b9ebeb99473dc25807'
COMPILED_DIMS = tuple(range(2, 17)) + (32, 34, 96, 100, 128, 784, 960)
VARIANTS = {
    'indexicon_rtree_point': ('rtree_point', 'R-tree (points)', None),
    'indexicon_rtree_mbr': ('rtree_mbr', 'R-tree (MBR)', None),
    'indexicon_kdtree_adaptive': ('kdtree', 'k-d tree (adaptive)', None),
    'indexicon_kdtree_round_robin': ('kdtree', 'k-d tree (round robin)', None),
    'indexicon_kdtree_longest_axis': ('kdtree', 'k-d tree (longest axis)', None),
    'indexicon_quadtree_pr': ('quadtree', 'quadtree (point region)', 2),
    'indexicon_quadtree_pseudo_median': ('quadtree', 'quadtree (pseudo-median)', 2),
    'indexicon_quadtree_longest_axis': ('quadtree', 'quadtree (longest axis)', 2),
    'indexicon_mxcif_quadtree': ('mxcif', 'MX-CIF quadtree (MBR)', 2),
    'indexicon_octree': ('octree', 'octree', 3),
}
BACKENDS = {key: 'indexicon_' + value[0] for key, value in VARIANTS.items()}
LABELS = {key: 'Indexicon ' + value[1] for key, value in VARIANTS.items()}


def supported(name, dimension):
    fixed = VARIANTS[name][2]
    return dimension == fixed if fixed is not None else dimension in COMPILED_DIMS


def metadata(name):
    return dict(display_name=LABELS[name],
                provenance='Indexicon ' + REVISION + '; original box API, exact L2 filter (inline coordinates in 2D/3D)',
                source_repairs=False, output_contract='point_ids_only',
                membership_contract='original_box_api_with_integer_ball_filter')
