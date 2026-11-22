"""Time requested algorithms even when their correctness admission fails."""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import time

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
WORK=PROJECT/"results/_queue-coverage-completion-20261030/workspace"
DATA=PROJECT/"results/_queue-indexicon-20261105/workspace/data"
PYTHON=PROJECT.parent/"SFC-Index/toolchains/esa-python/bin/python"
HIGH=("ESA_clustering","ESA_graph_embeddings","ESA_high_dimensional","ESA_uniform_points")
LOW=("input_scaling","radius_scaling","static","GeographyLarge","input_scaling_3d","radius_scaling_3d","Static3D",
     "2D_ESA_graph_embeddings","2D_ESA_uniform_points","2D_ESA_geographical")
ALGS=("esa_grid","esa_kiddo","esa_nabo","esa_neighbourhood","esa_orthtree","esa_vptree",
      "esa_nanoflann","esa_snn","esa_snn_rust","esa_sklearn_kd","esa_sklearn_ball")
COUNTS=Counter()
DONE=[]


def save(name,value):
    p=ROOT/name
    t=p.with_suffix(".tmp")
    t.write_text(json.dumps(value,indent=2)+"\n")
    t.replace(p)


def status(stage,**fields):
    save("status.json",dict(status=stage,completed=DONE,counts=COUNTS,cpu=1,workers=1,
                            measure_failed_correctness=True,updated_unix=time.time(),**fields))


def command(algorithm,path,bench):
    if algorithm=="MortonPlusDDim":
        cmd=[WORK/"build/dimensional/morton_plus_ddim_check",path,algorithm]
    elif algorithm=="esa_sprk_RUST_EXACT_DDIM":
        cmd=[ROOT/"sprk-driver/target/release/sprk-ddim",path,algorithm]
    else:
        cmd=[PYTHON,WORK/"tools/original_runner.py","--dimensional",path,algorithm]
    return [str(x) for x in cmd]+(["--bench"] if bench else [])


def job(algorithm,path,phase):
    start=time.monotonic()
    try:
        p=subprocess.run(command(algorithm,path,phase!="correctness"),capture_output=True,text=True,
                         timeout=180 if phase=="final" else 60)
        try:
            result=json.loads(p.stdout)
        except json.JSONDecodeError:
            result=dict(status="error",detail=(p.stdout+p.stderr)[-1500:])
        if p.returncode:
            result["returncode"]=p.returncode
            if "Unsupported" in p.stderr or "unsupported" in p.stdout:
                result["status"]="unsupported_input"
            elif result.get("status")=="success":result["status"]="error"
        return dict(result,wall_seconds=time.monotonic()-start)
    except subprocess.TimeoutExpired:
        return dict(status="timeout",wall_seconds=time.monotonic()-start)


def sample(source,dest):
    with source.open("rb") as f:
        head=f.read(8)
        if head==b"ESA2D01\0":
            d=2
            n,q=struct.unpack("<QQ",f.read(16))
        else:
            f.seek(0)
            d,n,q=struct.unpack("<IQQ",f.read(20))
        offset=f.tell()
        small=min(n,2000)
        points=f.read(small*d*4)
        choices=[i*(q-1)//max(1,min(q,4)-1) for i in range(min(q,4))]
        with dest.open("wb") as out:
            out.write(struct.pack("<IQQ",d,small,len(choices)))
            out.write(points)
            for i in choices:
                f.seek(offset+n*d*4+i*(d*4+16))
                out.write(f.read(d*4+16))
    return d


def campaign(name):
    m=DATA/name/"campaign.json"
    cases=json.loads(m.read_text())["cases"]
    algs=("MortonPlusDDim","esa_sprk_RUST_EXACT_DDIM") if name in HIGH else ALGS
    out=ROOT/name
    out.mkdir()
    files={row["id"]:(m.parent/row["path"]).resolve() for row in cases}
    dims={}
    for case in cases:
        path=files[case["id"]]
        with path.open("rb") as f:
            checksum=hashlib.file_digest(f,"sha256").hexdigest()
        if checksum!=(case.get("sha256") or case["conversion"]["sha256"]):
            raise ValueError(f"Checksum mismatch: {name} {case['id']}")
        with path.open("rb") as f:
            prefix=f.read(8)
            dims[case["id"]]=2 if prefix==b"ESA2D01\0" else struct.unpack("<I",prefix[:4])[0]
        if name in LOW and prefix==b"ESA2D01\0":
            converted=out/("dimensional-"+str(len(dims))+".bin")
            with path.open("rb") as source, converted.open("wb") as target:
                source.seek(8)
                target.write(struct.pack("<I",2))
                shutil.copyfileobj(source,target)
            files[case["id"]]=converted
    gates={}
    with (out/"jobs.jsonl").open("x",buffering=1) as log:
        def record(row):
            print(json.dumps(row),file=log)
            COUNTS[row["phase"]]+=1
            COUNTS[row["phase"]+"_"+row["status"]]+=1
        for d in sorted(set(dims.values())):
            case=min((row for row in cases if dims[row["id"]]==d),key=lambda row:row["n"])
            fixture=out/f"correctness-d{d}.bin"
            sample(files[case["id"]],fixture)
            for a in algs:
                status("correctness",campaign=name,dimension=d,algorithm=a)
                if a=="MortonPlusDDim" and d>16:
                    result=dict(status="unsupported_dimension",reason="MortonPlusDDim supports dimensions 1 through 16")
                else:result=job(a,fixture,"correctness")
                gates[d,a]=result["status"]
                record(dict(result,algorithm=a,case=case["id"],dimension=d,phase="correctness"))
        timed_out=set()
        for phase,reps in (("screen",1),("final",3)):
            jobs=[(case,a,rep) for case in files for a in algs for rep in range(reps)]
            random.Random(20261120).shuffle(jobs)
            for i,(case,a,rep) in enumerate(jobs,1):
                if i%10==1:status(phase,campaign=name,job=i,total_jobs=len(jobs))
                d=dims[case]
                admission=gates[d,a]
                if admission in ("unsupported_dimension","unsupported_input"):
                    result=dict(status=admission,wall_seconds=0)
                elif phase=="final" and (case,a) in timed_out:
                    result=dict(status="skipped_after_timeout",wall_seconds=0)
                else:
                    result=job(a,files[case],phase)
                    if phase=="final" and result["status"]=="timeout":timed_out.add((case,a))
                record(dict(result,algorithm=a,case=case,dimension=d,phase=phase,repetition=rep,
                            correctness_admission=admission,measure_failed_correctness=True))
    DONE.append(name)
    status("campaign_complete",campaign=name)


def main():
    os.sched_setaffinity(0,{1})
    for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","RAYON_NUM_THREADS","PARLAY_NUM_THREADS"):
        os.environ[key]="1"
    os.environ["PYTHONPATH"]=str(PROJECT.parent/"SFC-Index/code/third_party/esa2026")
    if (ROOT/"plan.json").exists():
        previous=json.loads((ROOT/"status.json").read_text())
        for name in previous.get("completed",[]):
            if (ROOT/name/"jobs.jsonl").exists():
                DONE.append(name)
                with (ROOT/name/"jobs.jsonl").open() as log:
                    for line in log:
                        row=json.loads(line)
                        COUNTS[row["phase"]]+=1
                        COUNTS[row["phase"]+"_"+row["status"]]+=1
    save("plan.json",dict(higher_dim=HIGH,higher_dim_algorithms=["MortonPlusDDim","esa_sprk_RUST_EXACT_DDIM"],
                         disk_campaigns=LOW,disk_algorithms=ALGS,cpu=1,measure_failed_correctness=True))
    try:
        if not (ROOT/"sprk-driver/target/release/sprk-ddim").exists():
            status("building")
            with (ROOT/"build.log").open("a") as log:
                subprocess.run(["python3",str(ROOT/"prepare_requested_queue.py")],stdout=log,stderr=subprocess.STDOUT,check=True)
        for name in (*HIGH,*LOW):
            if name in DONE:
                continue
            try:campaign(name)
            except Exception as error:
                save(name+"-failure.json",dict(error=str(error)))
                COUNTS["campaign_errors"]+=1
        status("complete_with_errors" if COUNTS["campaign_errors"] else "complete")
    except Exception as error:
        status("needs_attention",error=str(error))
        raise


if __name__=="__main__":
    main()
