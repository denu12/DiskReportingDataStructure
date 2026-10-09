"""Collect recorded outcomes, including failures; never impute timings."""
import argparse,csv,json,sys
from pathlib import Path
from algorithm_labels import metadata
from experiment_integrity import check_answer_counts
p=argparse.ArgumentParser();p.add_argument('state',type=Path);args=p.parse_args()
s=json.loads(args.state.read_text())
if s.get("answer_count_mismatches") or check_answer_counts(s):raise SystemExit('Answer counts disagree; refusing to export timings')
coverage={}
for row in s['results']:
 if row['status']=='success':coverage.setdefault(row['algorithm'],set()).add(row['case'])
configured=len(s.get('configured_cases',set(r['case'] for r in s['results'])))
fields=['display_name','provenance','source_repairs','algorithm','case','status','output_contract','repetition','wall_seconds','build_seconds','query_seconds','update_seconds','queries','answers','execution_backend','successful_cases','configured_cases']
w=csv.DictWriter(sys.stdout,fieldnames=fields);w.writeheader()
for row in s['results']:
 merged={'successful_cases':len(coverage.get(row['algorithm'],set())),'configured_cases':configured,'execution_backend':row.get('execution_backend',s.get('identity',{}).get('backend','unknown')),**metadata(row['algorithm']),**(row.get('result') or {}),**row};w.writerow({k:merged.get(k,'') for k in fields})
