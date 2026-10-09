"""Collect recorded outcomes, including failures; never impute timings."""
import argparse,csv,json,sys
from pathlib import Path
from algorithm_labels import metadata
p=argparse.ArgumentParser();p.add_argument('state',type=Path);args=p.parse_args()
s=json.loads(args.state.read_text());fields=['display_name','provenance','source_repairs','algorithm','case','status','output_contract','repetition','wall_seconds','build_seconds','query_seconds','update_seconds','queries','answers']
w=csv.DictWriter(sys.stdout,fieldnames=fields);w.writeheader()
for row in s['results']:
 merged={**metadata(row['algorithm']),**(row.get('result') or {}),**row};w.writerow({k:merged.get(k,'') for k in fields})
