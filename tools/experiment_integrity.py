"""Admission inputs and measurement integrity shared by both campaign runners."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import platform
import random
import struct

SCHEDULE_SEED = 20261009


def machine_identity(cpus):
    def read(path):
        try: return Path(path).read_text().strip()
        except OSError: return None
    info = read('/proc/cpuinfo') or ''
    return dict(kernel=platform.release(), machine=platform.machine(),
        cpu_models=sorted({line.split(':',1)[1].strip() for line in info.splitlines() if line.startswith('model name')}),
        microcode=sorted({line.split(':', 1)[1].strip() for line in info.splitlines() if line.startswith('microcode')}),
        governors={str(c): read(f'/sys/devices/system/cpu/cpu{c}/cpufreq/scaling_governor') for c in cpus},
        intel_no_turbo=read('/sys/devices/system/cpu/intel_pstate/no_turbo'),
        boost=read('/sys/devices/system/cpu/cpufreq/boost'))


def boundary_case(folder, dimension=2, format2d=True, dynamic=False):
    """Closed spheres, duplicates, zero radius and both uint32 grid edges."""
    top = 2**32-1
    def p(x, y, fill=0): return ((x, y)+tuple([fill]*max(0,dimension-2)))[:dimension]
    points = [p(0,0), p(0,0), p(3,4), p(4,3), p(5,0), p(5,1),
              p(top,top,top), p(top,top,top), p(top-3,top-4,top),
              p(100,100,100), p(103,104,100), p(100,105,100)]
    rng=random.Random(20261009+dimension)
    points.extend(tuple(rng.randrange(top+1) for _ in range(dimension)) for _ in range(max(1024,2*dimension)))
    queries = [(p(0,0),0), (p(0,0),25), (p(top,top,top),0),
               (p(top,top,top),25), (p(100,100,100),25),
               (p(0,0),dimension*top*top)]
    if dimension>=3:
        points += [(1,2,2)+tuple([0]*(dimension-3)),(2,3,6)+tuple([0]*(dimension-3))]
        queries += [(p(0,0),9),(p(0,0),49)]
    path = Path(folder)/f'boundary-duplicates-d{dimension}.bin'
    path.parent.mkdir(parents=True, exist_ok=True)
    events = [(2,c,r) for c,r in queries]
    if dynamic:
        events += [(1,p(0,0),0),(2,p(0,0),0),(0,p(0,0),0),(2,p(0,0),0)]
    with path.open('wb') as f:
        if format2d:
            f.write(struct.pack('<8sQQ', b'DRRDYN1\0' if dynamic else b'ESA2D01\0',len(points),len(events) if dynamic else len(queries)))
        else: f.write(struct.pack('<IQQ',dimension,len(points),len(queries)))
        for point in points: f.write(struct.pack('<'+'I'*dimension,*point))
        for kind,center,radius in events if dynamic else [(2,c,r) for c,r in queries]:
            if dynamic: f.write(struct.pack('<B',kind))
            f.write(struct.pack('<'+'I'*dimension,*center))
            f.write(struct.pack('<QQ',radius&((1<<64)-1),radius>>64))
    return dict(id=f'admission/boundary-duplicates-d{dimension}', suite='admission',
        dimension=dimension,n=len(points),queries=sum(k==2 for k,_,_ in events) if dynamic else len(queries),
        path=str(path.resolve()),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def check_answer_counts(state, previous=()):
    """Disagreement blocks all implicated measurements, without guessing a winner.

    Counts are a necessary cross-check, not a replacement for multiset admission.
    Correctness samples and full query sets are compared only when counts match.
    """
    groups = defaultdict(list)
    for source in [*previous, state]:
        for row in source['results']:
            result = row.get('result') or {}
            if row['status']=='success' and 'answers' in result and 'queries' in result:
                groups[(row['case'],result['queries'])].append((source is state,row))
    mismatches=[]
    for (case,queries),rows in groups.items():
        counts=sorted({r['result']['answers'] for _,r in rows})
        if len(counts)<2 or not any(current for current,_ in rows): continue
        mismatches.append(dict(case=case,queries=queries,answer_counts=counts))
        for current,row in rows:
            if current:
                row['status']='answer_count_mismatch'
                if state.get('phase')=='correctness': state['eligibility'][row['algorithm']]='excluded'
    state['answer_count_mismatches']=mismatches
    if mismatches:
        state['status']='needs_attention';state['needs_attention']=True
    return mismatches


def prior_phases(folder, phase):
    order=['correctness','screen','final','followup','contention']
    return [json.loads(p.read_text()) for name in order[:order.index(phase)]
            if (p:=Path(folder)/name/'state.json').exists()]
