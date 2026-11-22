"""Rerun PH-tree and PSI with matching disk and box inputs on one core."""

from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import struct
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT.parent
DISK = RESULTS / "_queue-indexicon-20261105/workspace/data"
SQUARE = (ROOT / "../../../SquareReportingDataStructure/results/square-full-2d-3d-20261106").resolve()
PREVIOUS = "drr-disk-adapters-parity-20261115.service"
ALGORITHMS = ("phtree", "psi_kd", "psi_orth", "psi_spac_z", "psi_spac_h")
MORE_3D = {
    "cgal_kd": "cgal_kd_3d", "pgm_multidimensional": "pgm_3d",
    **{f"lsi_{name}": "lsi_3d" for name in ("linear","quadratic","rstar","str")},
    **{f"indexicon_kdtree_{name}": "indexicon_kd_3d" for name in ("adaptive","round_robin","longest_axis")},
}
CUBE = ("pgm_multidimensional","psi_spac_z","psi_spac_h")
COUNTS = Counter()
COMPLETE = []


def save(name, value):
    path = ROOT / name
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def status(stage, **details):
    save("status.json", dict(status=stage, dimensions=[2, 3], cpu=1, workers=1,
                             updated_unix=time.time(), completed=COMPLETE, counts=COUNTS, **details))


def job(name, path, phase, geometry="disk"):
    if geometry == "square" and name == "pgm_multidimensional":
        exe = SQUARE.parents[1] / "build/square_pgm"
        backend = "pgm"
    else:
        exe = ROOT / "bin" / MORE_3D.get(name, "phtree" if name=="phtree" else "psi")
        backend = name
    start = time.monotonic()
    command = [str(exe), str(path), backend]
    if phase != "correctness":
        command.append("--bench")
    try:
        run = subprocess.run(command, capture_output=True, text=True, timeout=180 if phase == "final" else 60)
        if run.returncode == 0:
            result = json.loads(run.stdout)
            if "m" in result:
                result["answers"] = result["m"]
        else:
            result = dict(status="incorrect" if run.returncode == 2 else "error",
                          exit_code=run.returncode, detail=run.stderr[-1200:])
    except subprocess.TimeoutExpired:
        result = dict(status="timeout")
    return dict(result, algorithm=name, phase=phase, wall_seconds=time.monotonic()-start)


def record(stream, row, **fields):
    print(json.dumps(dict(row, **fields)), file=stream)
    COUNTS[row["phase"]] += 1
    COUNTS[f'{row["phase"]}_{row["status"]}'] += 1


def disk_header(dimension, n, q):
    return struct.pack("<8sQQ", b"ESA2D01\0", n, q) if dimension == 2 else struct.pack("<IQQ", dimension, n, q)


def fixtures():
    rng = random.Random(20261115)
    top = 2**32-1
    with tempfile.TemporaryDirectory() as work:
        path = Path(work) / "case.bin"
        for d in (2, 3):
            zero, limit = (0,)*d, (top,)*d
            points = [zero, limit, (1,)*d, (top,)+(0,)*(d-1)] + [(7,)*d]*202
            points += [tuple(rng.getrandbits(32) for _ in range(d)) for _ in range(1024)]
            radii = (0, 1, d, top**2-1, top**2, d*top**2-1, d*top**2, 2**128-1)
            disks = [(zero,r) for r in radii] + [(limit,r) for r in radii]
            disks += [(tuple(rng.getrandbits(32) for _ in range(d)), rng.getrandbits(65)) for _ in range(60)]
            boxes = [(zero, zero), (limit, limit), (zero, limit), ((7,)*d, (7,)*d)]
            vector = struct.Struct("<" + "I"*d)
            for data in ([], points):
                packed = b"".join(vector.pack(*p) for p in data)
                for geometry in ("disk", "square"):
                    if geometry == "disk":
                        payload = disk_header(d,len(data),len(disks)) + packed + b"".join(
                            vector.pack(*p) + radius.to_bytes(16,"little") for p,radius in disks)
                    else:
                        payload = struct.pack("<8sIQQ",b"SQUARE1\0",d,len(data),len(boxes)) + packed + b"".join(
                            vector.pack(*lo) + vector.pack(*hi) for lo,hi in boxes)
                    path.write_bytes(payload)
                    names = (*ALGORITHMS,*MORE_3D) if d==3 and geometry=="disk" and all(
                        (ROOT/"bin"/exe).exists() for exe in set(MORE_3D.values())) else ALGORITHMS
                    for name in names:
                        verdict = job(name,path,"correctness")
                        if verdict["status"] != "success":
                            raise RuntimeError(f"{d}D {geometry} fixture failed: {verdict}")
                        COUNTS["correctness"] += 1
                        COUNTS["correctness_success"] += 1


def sample_input(path, dest, d, case, geometry):
    n, q = case["n"],case["queries"]
    indices = [i*(q-1)//max(1,min(q,8)-1) for i in range(min(q,8))]
    if geometry == "square":
        header = struct.pack("<8sIQQ",b"SQUARE1\0",d,n,len(indices))
        query_bytes = d*8
    else:
        header = disk_header(d,n,len(indices))
        query_bytes = d*4+16
    point_bytes = d*4*n
    with path.open("rb") as source, dest.open("wb") as out:
        head_size = len(header)
        source.seek(head_size)
        out.write(header)
        left = point_bytes
        while left:
            chunk = source.read(min(left,1024*1024))
            if not chunk:
                raise ValueError(f"Truncated points in {path}")
            out.write(chunk)
            left -= len(chunk)
        for index in indices:
            source.seek(head_size + point_bytes + index*query_bytes)
            line = source.read(query_bytes)
            if len(line)!=query_bytes:
                raise ValueError(f"Truncated query in {path}")
            out.write(line)


def references(campaign, d):
    theater = "static-3d" if d == 3 else "small" if campaign.startswith("2D_ESA_") else "static"
    original = RESULTS / campaign / f"indexicon-l2-{theater}-20261105/final/state.json"
    disk = defaultdict(set)
    for row in json.loads(original.read_text())["results"]:
        if row["algorithm"] == "indexicon_rtree_point" and row["status"] == "success":
            result = row["result"]
            disk[row["case"]].add((result["queries"], result["answers"]))
    sources = defaultdict(lambda: defaultdict(set))
    with (SQUARE/campaign/"jobs.jsonl").open() as log:
        for line in log:
            row = json.loads(line)
            if row["phase"] == "final" and row["status"] == "success":
                if row["algorithm"] in ("scan","morton","morton_3d"):
                    sources[row["case"]][row["algorithm"]].add((row["queries"],row["m"]))
    square = {case:(r.get("scan") or r.get("morton_3d") or r.get("morton")) for case,r in sources.items()}
    return dict(disk=disk,square=square)


def campaign(name,d):
    status("checking_inputs",campaign=name,dimension=d)
    manifest = DISK/name/"campaign.json"
    cases = {c["id"]:c for c in json.loads(manifest.read_text())["cases"]}
    square = json.loads((SQUARE/name/"inputs.json").read_text())
    paths = {
        "disk":{key: (manifest.parent/case["path"]).resolve() for key,case in cases.items()},
        "square":{key: SQUARE/name/"inputs"/case["path"] for key,case in square.items()},
    }
    roster = {"disk": (*ALGORITHMS,*MORE_3D) if d==3 else ALGORITHMS,
              "square": CUBE if d==3 else ()}
    expected = references(name,d)
    for geometry, inputs in paths.items():
        if set(inputs)!=set(cases):
            raise ValueError(f"Unmatched {geometry} input IDs in {name}")
        for key,path in inputs.items():
            case = cases[key] if geometry == "disk" else square[key]
            with path.open("rb") as file:
                checksum = hashlib.file_digest(file,"sha256").hexdigest()
            if checksum != (case.get("sha256") or case["conversion"]["sha256"]):
                raise ValueError(f"Input checksum mismatch for {geometry} {name} {key}")
            if len(expected[geometry].get(key,()))!=1:
                raise ValueError(f"Missing or inconsistent answer counts for {geometry} {name} {key}")
    out = ROOT/name
    out.mkdir()
    sample = min(cases,key=lambda key:cases[key]["n"])
    with (out/"jobs.jsonl").open("x",buffering=1) as log:
        for geometry, inputs in paths.items():
            if not roster[geometry]:
                continue
            exact = out/f"{geometry}-correctness.bin"
            sample_input(inputs[sample],exact,d,cases[sample],geometry)
            for algorithm in roster[geometry]:
                result = job(algorithm,exact,"correctness",geometry)
                record(log,result,case=sample,geometry=geometry)
                if result["status"]!="success":
                    raise RuntimeError(f"{name} {geometry} correctness failed: {result}")
        for phase,repeats in (("screen",1),("final",3)):
            jobs = [(geometry,case,algorithm,rep) for geometry,names in roster.items()
                    for case in cases for algorithm in names for rep in range(repeats)]
            rng = random.Random(20261115)
            rng.shuffle(jobs)
            for number,(geometry,case,algorithm,rep) in enumerate(jobs,1):
                if number%10==1:
                    status(phase,campaign=name,dimension=d,job=number,total_jobs=len(jobs))
                result = job(algorithm,paths[geometry][case],phase,geometry)
                if result["status"]=="success" and (result["queries"],result["answers"]) not in expected[geometry][case]:
                    result["status"]="answer_count_mismatch"
                    result["expected"]=next(iter(expected[geometry][case]))
                record(log,result,case=case,geometry=geometry,repetition=rep)
    COMPLETE.append(name)


def report(plan):
    results = defaultdict(list)
    for name,d in plan:
        data = defaultdict(lambda: defaultdict(list))
        with (ROOT/name/"jobs.jsonl").open() as log:
            for line in log:
                row = json.loads(line)
                if row["phase"] == "final" and row["status"] == "success":
                    data[row["case"],row["algorithm"]][row["geometry"]].append(row["query_seconds"])
        with (SQUARE/name/"jobs.jsonl").open() as log:
            for line in log:
                row=json.loads(line)
                key=(row["case"],row["algorithm"])
                if d==3 and row["algorithm"] in CUBE:
                    continue
                if key in data and row["phase"]=="final" and row["status"]=="success" and row["correctness_admission"]=="passed":
                    data[key]["square"].append(row["query_seconds"])
        for (_,algorithm),times in data.items():
            disk,square = times["disk"],times["square"]
            if len(disk)==len(square)==3 and min(disk+square)>0:
                results[d,algorithm].append(statistics.median(disk)/statistics.median(square))
    save("report.json", {
        str(d): {algorithm: dict(matched_cases=len(v),disk_over_square=statistics.geometric_mean(v) if v else None,
                                 within_30_percent=sum(.7<ratio<1.3 for ratio in v))
                 for algorithm in ((*ALGORITHMS,*MORE_3D) if d==3 else ALGORITHMS) for v in [results[d,algorithm]]}
        for d in (2,3)})


def main():
    if sys.argv[1:] == ["--fixtures"]:
        fixtures()
        print(dict(COUNTS))
        return
    os.sched_setaffinity(0,{1})
    plan = json.loads((SQUARE/"plan.json").read_text())["campaigns"]
    with (ROOT/"plan.json").open("x") as file:
        json.dump(dict(campaigns=plan,disk_2d=ALGORITHMS,disk_3d=(*ALGORITHMS,*MORE_3D),
                       square_3d=CUBE,cpu=1,repetitions=[1,3]),file,indent=2)
    status("waiting", behind=PREVIOUS)
    while subprocess.run(["systemctl","--user","is-active","--quiet",PREVIOUS]).returncode == 0:
        time.sleep(60)
    status("building")
    try:
        with (ROOT/"build.log").open("x") as log:
            subprocess.run(["bash",str(ROOT/"build_ph_psi.sh")],stdout=log,stderr=subprocess.STDOUT,check=True)
        status("correctness")
        fixtures()
        for name,d in plan:
            campaign(name,d)
        report(plan)
        status("complete")
    except Exception as error:
        status("needs_attention",error=str(error))
        raise


if __name__ == "__main__":
    main()
