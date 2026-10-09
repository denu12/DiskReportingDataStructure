"""Resolve dimensional benchmark executables without importing data preparation."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]

def command(algorithm):
    if algorithm == "esa_sprk_CHEATING_IDS_ONLY":return [str(ROOT/"build/ddim-rust/release/ddim-sprk-ids-check")]
    if algorithm == "Morton3D":return [str(ROOT/"build/dimensional/morton_3d_check")]
    if algorithm == "morton_d_dim":return [str(ROOT/"build/dimensional/morton_ddim_check")]
    manual=['chan_sss_ddim_MANUALLY_ADAPTED','stann_fr_ddim_MANUALLY_ADAPTED']
    rust=['esa_sprk','esa_kiddo','esa_nabo','esa_neighbourhood','esa_vptree','esa_orthtree','esa_grid']
    if algorithm in manual:return [str(ROOT/'build/dimensional/ddim_check')]
    if algorithm in rust:return [str(ROOT/'build/ddim-rust/release/ddim-esa-check')]
    if algorithm=='esa_snn_rust':return [str(ROOT/'build/ddim-rust/release/ddim-snn-check')]
    if algorithm in ['esa_sklearn_kd','esa_sklearn_ball','esa_snn','brute_force']:
        return [sys.executable,str(ROOT/'src/runner/dimensional/python_check.py')]
    kind='boost' if algorithm.startswith('boost_') else {'ann_fr':'ann','cgal_kd':'cgal','esa_nanoflann':'nano'}[algorithm]
    return [str(ROOT/'build/dimensional'/('check_'+kind))]
