"""Canonical 2D binary routing for preparation, preflight and execution."""
def binary(algorithm):
    if algorithm in {'MortonPlus3D', 'esa_sprk_RUST_EXACT_3D', 'MortonPlusDDim'}:
        raise ValueError("Dimensional-runner algorithm: " + algorithm)
    if algorithm in {'Morton', 'MortonSIMD', 'MortonPlusCPP'}:
        return 'morton_cpp'
    if algorithm == 'esa_sprk_RUST_EXACT':
        return 'sprk_rust_exact'
    if algorithm in {'esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS', 'esa_sprk_FAST_EXACT', 'MortonPlusRust'}:
        raise ValueError('Retired algorithm: ' + algorithm + '; prepare a fresh campaign')
    return 'esa_runner_pargeo' if algorithm == 'pargeo' else 'esa_runner'
