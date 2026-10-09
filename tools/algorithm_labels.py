"""Canonical publication labels; machine IDs remain stable for provenance."""
LABELS = {
 'Morton': 'Morton', 'MortonSIMD': 'MortonSIMD', 'Morton3D': 'Morton3D',
 'morton_d_dim': 'MortonDDim', 'naive': 'Brute force', 'brute_force': 'Brute force',
 'boost_lin': 'Boost linear', 'boost_quad': 'Boost quadratic', 'boost_star': 'Boost R-star',
 'cgal_rt': 'CGAL range tree', 'cgal_kd': 'CGAL k-d tree',
 'thst_quad': 'THST quadtree', 'thst_rtree': 'THST R-tree',
 'pargeo': 'ParGeo', 'pam': 'PAM', 'pkd': 'Pkd-tree',
 'chan_sss': 'Chan', 'chan_sss_ddim_MANUALLY_ADAPTED': 'Chan',
 'chan_sss_dyn_ADAPTED_DYNAMIC': 'Chan',
 'ann_fr': 'ANN', 'stann_fr': 'STANN', 'stann_fr_ddim_MANUALLY_ADAPTED': 'STANN',
 'esa_sprk': 'SPRK', 'esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS': 'SPRK',
 'esa_sprk_CHEATING_IDS_ONLY': 'SPRK (cheating)',
 'esa_kiddo': 'Kiddo', 'esa_nabo': 'Nabo', 'esa_neighbourhood': 'Neighbourhood',
 'esa_vptree': 'Acap VP-tree', 'esa_orthtree': 'Orthtree', 'esa_grid': 'Grid',
 'esa_sklearn_kd': 'scikit-learn k-d tree', 'esa_sklearn_ball': 'scikit-learn ball tree',
 'esa_snn': 'SNN (Python)', 'esa_snn_rust': 'SNN (Rust)', 'esa_nanoflann': 'nanoflann',
 'boost_lin_dyn': 'Boost linear', 'boost_quad_dyn': 'Boost quadratic',
 'boost_star_dyn': 'Boost R-star', 'kiddo_mutable_dyn_UPSTREAM': 'Kiddo mutable',
 'nanoflann_dyn_UPSTREAM': 'nanoflann', 'pkd_dyn_UPSTREAM': 'Pkd-tree',
 'thst_rtree_dyn_UPSTREAM': 'THST R-tree', 'thst_quad_dyn_UPSTREAM': 'THST quadtree',
}
LOCAL = {'Morton','MortonSIMD','Morton3D','morton_d_dim','naive','brute_force'}
REIMPLEMENTED = {'chan_sss','chan_sss_ddim_MANUALLY_ADAPTED','chan_sss_dyn_ADAPTED_DYNAMIC'}
MODIFIED = {'stann_fr','stann_fr_ddim_MANUALLY_ADAPTED',
            'esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS','esa_kiddo','esa_grid','esa_neighbourhood'}
PATCHED = {'esa_kiddo','esa_grid','esa_neighbourhood'}

def metadata(algorithm):
    label = LABELS[algorithm]
    if algorithm not in LOCAL and algorithm != 'esa_sprk_CHEATING_IDS_ONLY':
        label += ' (adapted)'
    provenance = ('local implementation' if algorithm in LOCAL else
                  'local implementation of published technique' if algorithm in REIMPLEMENTED else
                  'modified upstream source and local adapter' if algorithm in MODIFIED else
                  'upstream index with local adapter')
    return dict(display_name=label, provenance=provenance,
                source_repairs=algorithm in PATCHED,
                output_contract='point_ids_only' if algorithm == 'esa_sprk_CHEATING_IDS_ONLY' else 'integer_points')

def display_name(algorithm):
    return metadata(algorithm)['display_name']
