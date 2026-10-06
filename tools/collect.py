"""Collect recorded outcomes, including failures; never impute timings."""
import argparse,csv,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('state',type=Path);args=p.parse_args()
s=json.loads(args.state.read_text());fields=['algorithm','case','status','repetition','wall_seconds','build_seconds','query_seconds','update_seconds','queries','answers']
w=csv.DictWriter(sys.stdout,fieldnames=fields);w.writeheader()
for row in s['results']:
 merged={**row,**(row.get('result') or {})};w.writerow({k:merged.get(k,'') for k in fields})
