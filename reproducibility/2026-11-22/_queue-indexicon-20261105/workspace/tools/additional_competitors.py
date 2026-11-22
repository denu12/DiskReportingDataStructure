"""Original implementations added October 2026; no replacement algorithms."""
import indexicon_competitors as indexicon

BACKENDS = {
    'phtree':'phtree', 'pgm_multidimensional':'pgm',
    'psi_kd':'psi', 'psi_orth':'psi', 'psi_spac_z':'psi', 'psi_spac_h':'psi',
    'lsi_linear':'spatialindex', 'lsi_quadratic':'spatialindex',
    'lsi_rstar':'spatialindex', 'lsi_str':'spatialindex',
}
LABELS = {
    'phtree':'PH-tree', 'pgm_multidimensional':'Multidimensional PGM-index',
    'psi_kd':'PSI k-d tree', 'psi_orth':'P-Orth tree',
    'psi_spac_z':'SPaC-Z tree', 'psi_spac_h':'SPaC-H tree',
    'lsi_linear':'libspatialindex linear', 'lsi_quadratic':'libspatialindex quadratic',
    'lsi_rstar':'libspatialindex R-star', 'lsi_str':'libspatialindex STR',
}
BACKENDS.update(indexicon.BACKENDS)
LABELS.update(indexicon.LABELS)

def metadata(name):
    if name in indexicon.BACKENDS: return indexicon.metadata(name)
    if name == 'pgm_multidimensional':
        return dict(display_name=LABELS[name]+' (adapted)', provenance='original PGM index with coarse coordinate cells, original-ID mapping and documented iterator fixes', source_repairs=True, output_contract='point_ids_only', membership_contract='closed_integer_ball')
    return dict(display_name=LABELS[name],
                provenance='pinned unmodified upstream index with file-format and box-to-ball adapter',
                source_repairs=False,
                output_contract='point_ids_only' if name=='phtree' or name.startswith('lsi_') else 'integer_points',
                membership_contract='original_box_api_with_integer_ball_filter')

# Dimensions present in the prepared campaigns. Upstream SPaC encoders are 2D/3D.
COMPILED_DIMS = set(range(2,17)) | {32,34,96,100,128,784,960}
def supported(name, dimension):
    if name in indexicon.BACKENDS: return indexicon.supported(name, dimension)
    if name == 'pgm_multidimensional': return dimension in set(range(2,17)) | {32}
    if name.startswith('lsi_'): return dimension >= 2
    if name == 'phtree': return dimension in COMPILED_DIMS and dimension < 64
    if name == 'psi_kd': return dimension in COMPILED_DIMS and dimension < 256
    if name == 'psi_orth': return 2 <= dimension <= 8
    return dimension in (2,3)
