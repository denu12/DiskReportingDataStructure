"""Delete superseded disk observations only after a usable newer result exists."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import time

RANKS = [('_queue-disk-remaining-',200),('_queue-disk-version-repair-',190),('_queue-snn-higherdim-recovery-',180),
 ('_queue-higherdim-missing-indexicon-',170),('_queue-measure-inexact-',160),
 ('_queue-ph-psi-',150),('_queue-disk-adapters-parity-',140),('_queue-disk-adapters-2d-',130),
 ('indexicon-l2-',120),('coverage-completion-',90),('original-all-',60),
 ('publication-remaining-',40),('ddim-all-three-sprk-',65),('additional-',80),
 ('reporting-adapted-',85)]


def rank(run):
    return next((value for prefix,value in RANKS if run.startswith(prefix)),
                20 if re.search(r'2026(?:10|11)\d{2}',run) and not run.startswith('_queue-') else 0)


def replacements(selection, queues):
    selected={}
    if selection:
        for p in json.loads(selection.read_text())['pairs']:
            if rank(p['run'])>=140 and p['outcome'] in ('complete','timeout_resolved'):
                selected[p['campaign'],p['algorithm'],p['case']]=p['run']
    for queue in queues:
        history={}
        files=list(queue.glob('*/jobs.jsonl'))+([queue/'jobs.jsonl'] if (queue/'jobs.jsonl').exists() else [])
        for file in files:
            for line in file.open():
                row=json.loads(line)
                if row.get('geometry','disk')!='disk' or row['phase']=='correctness':continue
                history.setdefault((row.get('campaign',file.parent.name),row['algorithm'],row['case']),[]).append(row)
        for key,rows in history.items():
            good=[r for r in rows if r['phase']=='final' and r['status'] in ('success','incorrect','answer_count_mismatch') and isinstance((r.get('result') or r).get('query_seconds'),(int,float))]
            if len({r.get('repetition') for r in good})>=3 or any('timeout' in r['status'] for r in rows):
                if rank(queue.name)>rank(selected.get(key,'')):selected[key]=queue.name
    return selected


def obsolete(row,campaign,run,selected):
    newer=selected.get((row.get('campaign',campaign),row.get('algorithm'),row.get('case')))
    if not newer:newer=selected.get(('*',row.get('algorithm'),row.get('case')))
    return newer and 0<rank(run)<rank(newer) and row.get('geometry','disk')=='disk'


def filter_content(content,campaign,run,selected,path):
    """Return changed content and job-directory prefixes to remove."""
    deleted=[]
    if path.endswith('.csv'):
        reader=csv.DictReader(io.StringIO(content))
        if not reader.fieldnames or not {'algorithm','case'}.issubset(reader.fieldnames):return content,deleted
        rows=list(reader);deleted=[r for r in rows if obsolete(r,campaign,run,selected)]
        if deleted:
            output=io.StringIO();writer=csv.DictWriter(output,fieldnames=reader.fieldnames);writer.writeheader()
            writer.writerows(r for r in rows if not obsolete(r,campaign,run,selected))
            return output.getvalue(),deleted
        return content,deleted
    if path.endswith('.jsonl'):
        lines=[]
        for line in content.splitlines():
            try:row=json.loads(line)
            except ValueError:lines.append(line);continue
            if isinstance(row,dict) and obsolete(row,campaign,run,selected):deleted.append(row)
            else:lines.append(line)
        return ('\n'.join(lines)+'\n' if deleted else content),deleted
    if not path.endswith('.json'):return content,deleted
    try:data=json.loads(content)
    except ValueError:return content,deleted
    if isinstance(data,list) and all(isinstance(r,dict) for r in data):
        deleted=[r for r in data if obsolete(r,campaign,run,selected)]
        if deleted:return json.dumps([r for r in data if not obsolete(r,campaign,run,selected)],indent=2)+'\n',deleted
    if isinstance(data,dict) and isinstance(data.get('results'),list):
        deleted=[r for r in data['results'] if obsolete(r,campaign,run,selected)]
        if deleted:
            data['results']=[r for r in data['results'] if not obsolete(r,campaign,run,selected)]
            data['superseded_result_rows_deleted']=data.get('superseded_result_rows_deleted',0)+len(deleted)
            data['status']='superseded_partial' if data['results'] else 'superseded'
            return json.dumps(data,indent=2)+'\n',deleted
    return content,deleted


def live(base,selected,apply):
    stats=Counter();changes=[]
    for campaign in sorted({k[0] for k in selected}):
        for run in (base/campaign).iterdir() if (base/campaign).exists() else []:
            if not run.is_dir() or not rank(run.name):continue
            for path in run.glob('*/state.json'):
                old=path.read_text();new,deleted=filter_content(old,campaign,run.name,selected,str(path))
                if not deleted:continue
                jobs=set()
                for row in deleted:
                    if row.get('log'):
                        # Resolve by known phase/jobs directory, not a path supplied by a row.
                        job=path.parent/'jobs'/Path(row['log']).parent.name
                        if job.is_dir():jobs.add(job)
                stats['state_rows_deleted']+=len(deleted);stats['job_directories_deleted']+=len(jobs)
                changes.append(dict(path=str(path.relative_to(base)),rows=len(deleted),before_sha256=hashlib.sha256(old.encode()).hexdigest(),after_sha256=hashlib.sha256(new.encode()).hexdigest()))
                if apply:
                    temporary=path.with_suffix('.pruning');temporary.write_text(new);temporary.replace(path)
                    for job in jobs:
                        assert job.resolve().is_relative_to(base.resolve()) and job.parent.name=='jobs'
                        shutil.rmtree(job)
    for queue in base.glob('_queue-*'):
        if not rank(queue.name):continue
        for path in list(queue.glob('*/jobs.jsonl'))+([queue/'jobs.jsonl'] if (queue/'jobs.jsonl').exists() else []):
            old=path.read_text();new,deleted=filter_content(old,path.parent.name,queue.name,selected,str(path))
            if deleted:
                stats['queue_rows_deleted']+=len(deleted)
                changes.append(dict(path=str(path.relative_to(base)),rows=len(deleted)))
                if apply:
                    temporary=path.with_suffix('.pruning');temporary.write_text(new);temporary.replace(path)
    return dict(stats=stats,changes=changes)


def snapshot(base,selected,apply):
    index=json.loads((base/'index.json').read_text());stats=Counter();phases=[]
    # Archived flat exports may omit their campaign directory. Match only
    # unambiguous algorithm/case identities, and only in older captured sources.
    fallback={};campaigns={}
    for (campaign,algorithm,case),run in selected.items():
        key='*',algorithm,case
        campaigns.setdefault(key,set()).add(campaign)
        if key not in fallback or rank(run)>rank(fallback[key]):fallback[key]=run
    selected={**selected,**{k:v for k,v in fallback.items() if len(campaigns[k])==1}}
    for bundle in index['bundles']:
        path=base/bundle['path']
        with gzip.open(path,'rt') as f:records=[json.loads(line) for line in f]
        drops=set();changed=False
        for record in records:
            parts=Path(record['path']).parts
            if len(parts)<2:continue
            campaign,run=parts[:2]
            if campaign.startswith('_queue-'):
                run=campaign;campaign=parts[1]
            if not rank(run):
                if bundle['path'].split('/')[0] not in ('historical','earlier-export','archived-validation'):continue
                run='archived-export-20261001'
            new,deleted=filter_content(record['content'],campaign,run,selected,record['path'])
            if deleted:
                stats['measurement_rows_deleted']+=len(deleted);changed=True
                record['content']=new
                # Original hash still describes pre-redaction source bytes; mark the edit explicitly.
                record['superseded_rows_deleted']=record.get('superseded_rows_deleted',0)+len(deleted)
                record['content_sha256']=hashlib.sha256(new.encode()).hexdigest()
                for row in deleted:
                    if row.get('log'):
                        prefix=str(Path(record['path']).parent/'jobs'/Path(row['log']).parent.name)+'/'
                        drops.add(prefix)
        kept=[]
        for record in records:
            if any(record['path'].startswith(prefix) for prefix in drops):stats['job_artifact_files_deleted']+=1;continue
            kept.append(record)
            if record['path'].endswith('/state.json'):
                try:s=json.loads(record['content'])
                except ValueError:continue
                rows=s.get('results',[])
                if rows:phases.append(dict(source=bundle['path'].split('/')[0],path=record['path'],status=s.get('status'),rows=len(rows),outcomes=dict(Counter(r.get('status','unknown') for r in rows)),algorithms=sorted({r.get('algorithm','unknown') for r in rows})))
        if changed:
            stats['bundles_changed']+=1
            if apply:
                temporary=path.with_suffix('.pruning')
                with temporary.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as out:
                    for record in kept:out.write((json.dumps(record,separators=(',',':'),ensure_ascii=False)+'\n').encode())
                temporary.replace(path)
                bundle.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),files=len(kept),source_bytes=sum(r['original_bytes'] for r in kept),compressed_bytes=path.stat().st_size)
    if apply:
        index['phases']=phases;index['total_files']=sum(x['files'] for x in index['bundles']);index['total_phase_rows']=sum(x['rows'] for x in phases)
        index['superseded_results_pruned_unix']=time.time()
        index.setdefault('notes',[]).append('Superseded disk measurements removed at user request. Edited records have content_sha256 and superseded_rows_deleted; original_sha256 remains the pre-redaction, pre-pruning source identity.')
        (base/'index.json').write_text(json.dumps(index,indent=2)+'\n')
    return dict(stats=stats)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',type=Path)
    parser.add_argument('--queue',type=Path,action='append',default=[])
    parser.add_argument('--live',type=Path,action='append',default=[])
    parser.add_argument('--snapshot',type=Path,action='append',default=[])
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--report',type=Path)
    parser.add_argument('--replacement-index',type=Path)
    args=parser.parse_args()
    selected=replacements(args.selection,args.queue)
    if args.replacement_index:
        for row in json.loads(args.replacement_index.read_text()):selected[tuple(row['key'])]=row['run']
    report=dict(applied=args.apply,replacement_cases=len(selected),live={},snapshots={})
    for base in args.live:report['live'][str(base)]=live(base,selected,args.apply)
    for base in args.snapshot:report['snapshots'][str(base)]=snapshot(base,selected,args.apply)
    if args.report:args.report.write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(applied=args.apply,replacement_cases=len(selected),live={k:v['stats'] for k,v in report['live'].items()},snapshots={k:v['stats'] for k,v in report['snapshots'].items()}),indent=2))


if __name__=='__main__':main()
