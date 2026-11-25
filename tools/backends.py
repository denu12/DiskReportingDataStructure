"""Resolve dimensional benchmark executables without importing data preparation."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]

def command(algorithm):
    if algorithm == 'esa_sprk_RUST_EXACT_DDIM':
        return [str(ROOT/'build/sprk-ddim/release/sprk-ddim')]
    from original_runner import RUST, PYTHON, UNSUPPORTED, FOREIGN, POSTGRES
    if algorithm in RUST | PYTHON | UNSUPPORTED | set(FOREIGN) | POSTGRES:
        return [sys.executable,str(ROOT/"tools/original_runner.py"),"--dimensional"]
    if algorithm == "MortonPlusDDim":return [str(ROOT/"build/dimensional/morton_plus_ddim_check")]
    if algorithm == "MortonPlus3D":return [str(ROOT/"build/dimensional/morton_plus_3d_check")]
    if algorithm == "esa_sprk_RUST_EXACT_3D":return [str(ROOT/"build/ddim-rust/release/sprk-adapted-3d-check")]
    if algorithm == "esa_sprk_CHEATING_IDS_ONLY":return [str(ROOT/"build/ddim-rust/release/ddim-sprk-ids-check")]
    if algorithm == "MortonSIMD3D":return [str(ROOT/"build/dimensional/morton_simd_3d_check")]
    if algorithm == "Morton3D":return [str(ROOT/"build/dimensional/morton_3d_check")]
    if algorithm == "morton_d_dim":return [str(ROOT/"build/dimensional/morton_ddim_check")]
    if algorithm.startswith('boost_'):return [str(ROOT/'build/dimensional/check_boost')]
    raise ValueError('Unknown dimensional backend: '+algorithm)
