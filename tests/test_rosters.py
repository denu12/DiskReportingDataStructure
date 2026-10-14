"""Keep default campaign families aligned without launching measurements."""
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/esa')]
from workloads import STATIC, STATIC_3D, DIMENSIONAL, DYNAMIC, validate_roster
from algorithm_labels import metadata
from backends import command
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location('esa_runner', ROOT/'tools/esa/run.py')
runner = module_from_spec(spec); spec.loader.exec_module(runner)

class Rosters(unittest.TestCase):
    def test_campaigns_match_defaults(self):
        for theater, expected in [('static',STATIC),('small',STATIC),('static-3d',STATIC_3D),('d-dim',DIMENSIONAL),('dynamic',DYNAMIC)]:
            validate_roster(expected)
            for path in (ROOT/'theaters'/theater/'campaigns').glob('*/campaign.json'):
                with self.subTest(path=path):
                    definition=json.loads(path.read_text())
                    if 'algorithms' in definition:self.assertEqual(definition['algorithms'],expected)
            for name in expected:self.assertTrue(metadata(name)['display_name'])
    def test_invalid_rosters(self):
        for names in [['Morton','Morton'], ['esa_sprk_FAST_EXACT'], ['esa_sprk'], ['MortonPlusRust'], ['Morton','MortonSIMD','MortonPlusCPP','Morton3D'], ['esa_sprk_RUST_EXACT','esa_sprk_RUST_EXACT_3D','esa_sprk_CHEATING_IDS_ONLY']]:
            with self.subTest(names=names), self.assertRaises(ValueError):validate_roster(names)
    def test_dimension_boundaries(self):
        for d in [1,2,3,4,16,17,32,34,960]:
            case={'dimension':d}
            self.assertEqual(runner.supported('MortonPlusDDim',case,False),d<=16)
            self.assertEqual(runner.supported('morton_d_dim',case,False),d<=16)
            self.assertEqual(runner.supported('esa_sprk_RUST_EXACT_3D',case,False),d==3)
            self.assertEqual(runner.supported('esa_sprk_CHEATING_IDS_ONLY',case,False),d in set(range(2,17))|{32})
        self.assertNotIn('Morton3D',DIMENSIONAL)
        self.assertNotIn('MortonPlus3D',DIMENSIONAL)
        for name in DIMENSIONAL+STATIC_3D:self.assertTrue(command(name))
    def test_all_competitors_enabled(self):
        self.assertEqual(json.loads((ROOT/'config/disabled-algorithms.json').read_text())['algorithms'],[])
        for roster in [STATIC,STATIC_3D,DIMENSIONAL]:
            self.assertTrue({'boost_lin','boost_quad','boost_star'}<=set(roster))

if __name__=='__main__':unittest.main()
