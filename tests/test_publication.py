"""Check unlimited budgets and safe measurement exports."""
import json,math,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from budget import budget
from export_measurements import clean,files
class Publication(unittest.TestCase):
 def test_budget(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'config').mkdir();config=p/'config/execution.json'
   config.write_text(json.dumps({'stages':{'final':{'budget_seconds':None,'timeout_seconds':180}}}))
   a=SimpleNamespace(base=p,run='check',campaign='test',phase='final')
   with budget(a):
    self.assertTrue(math.isinf(a.deadline))
    self.assertNotIn('Infinity',(p/'results/_budgets/check.json').read_text())
   ledger=json.loads((p/'results/_budgets/check.json').read_text())
   self.assertGreaterEqual(ledger['stages']['final'],0)
   self.assertEqual(ledger['sessions'][0]['status'],'closed')
   config.write_text(json.dumps({'stages':{'final':{'budget_seconds':1,'timeout_seconds':180}}}))
   with self.assertRaisesRegex(RuntimeError,'exhausted'):
    with budget(a):pass
 def test_redaction(self):
  self.assertEqual(clean('/home/person/project 192.168.77.2'),'<HOME>/project <PRIVATE-IP>')
  self.assertEqual(json.loads(clean(json.dumps({'hostname':'private','path':r'C:\Users\person\project'})))['hostname'],'<REDACTED>')
  with self.assertRaises(ValueError):clean('ghp_'+'a'*30)
 def test_inputs_and_workspace_excluded(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'workspace').mkdir();(p/'workspace/state.json').write_text('{}')
   (p/'state.json').write_text('{}');(p/'input.bin').write_bytes(b'input')
   self.assertEqual([x.name for x in files(p)],['state.json'])
if __name__=='__main__':unittest.main()
