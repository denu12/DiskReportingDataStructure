"""Rerun the updated 2D disk adapters on the original Archie inputs."""

from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import struct
import subprocess
import time


ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "_queue-indexicon-20261105/workspace/data"
CAMPAIGNS = (
    "input_scaling", "radius_scaling", "static", "GeographyLarge",
    "2D_ESA_graph_embeddings", "2D_ESA_uniform_points", "2D_ESA_geographical",
)
ALGORITHMS = {
    "pgm_multidimensional": "pgm_multidimensional",
    "phtree": "phtree",
    "lsi_str": "spatialindex",
    "lsi_rstar": "spatialindex",
    "cgal_kd": "cgal_kd",
    "cgal_rt": "cgal_rt",
    "lsi_linear": "spatialindex",
    "lsi_quadratic": "spatialindex",
    "pam": "pam",
    "pargeo": "pargeo",
    "psi_kd": "psi",
    "psi_orth": "psi",
    "psi_spac_h": "psi",
    "psi_spac_z": "psi",
    "thst_quad": "thst",
    "thst_rtree": "thst",
    "indexicon_kdtree_adaptive": "indexicon_kdtree",
    "indexicon_kdtree_longest_axis": "indexicon_kdtree",
    "indexicon_kdtree_round_robin": "indexicon_kdtree",
    "indexicon_quadtree_longest_axis": "indexicon_quadtree",
    "indexicon_quadtree_pseudo_median": "indexicon_quadtree",
    "indexicon_mxcif_quadtree": "indexicon_mxcif",
}
SQUARE = ROOT.parents[2] / "SquareReportingDataStructure"
SQUARE_RUN = SQUARE / "results/square-full-2d-3d-20261106"
SQUARE_FOLLOWUP = SQUARE / "results/square-rectangle-followup-2d-20261113"
SQUARE_EXES = {
    "pargeo": SQUARE / "build-rectangle/square_pargeo",
    "pgm_multidimensional": SQUARE / "build/square_pgm",
}
SQUARE_NAMES = {"cgal_rt": "cgal_range", "pgm_multidimensional": "pgm", "thst_quad": "thst_quadtree"}
COUNTS = Counter()
COMPLETE = []
START = time.time()


def write(name, value):
    path = ROOT / name
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def status(stage, **details):
    write("status.json", dict(status=stage, dimensions=[2], cpu=1, workers=1,
                             started_unix=START, updated_unix=time.time(),
                             completed=COMPLETE, counts=COUNTS, **details))


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def job(name, path, phase, *, square=False, **fields):
    exe = SQUARE_EXES[name] if square else ROOT / "bin" / ALGORITHMS[name]
    backend = SQUARE_NAMES.get(name, name) if square else name
    cmd = [str(exe), str(path), backend]
    if phase != "correctness":
        cmd.append("--bench")
    row = dict(algorithm=name, phase=phase, **fields)
    start = time.monotonic()
    try:
        process = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=180 if phase == "final" else 60)
        if process.returncode == 0:
            row.update(json.loads(process.stdout))
            row["algorithm"] = name
        else:
            row.update(status="incorrect" if process.returncode == 2 else "error",
                       returncode=process.returncode, detail=(process.stdout + process.stderr)[-1500:])
    except subprocess.TimeoutExpired:
        row["status"] = "timeout"
    return dict(row, wall_seconds=time.monotonic() - start)


def record(log, row):
    print(json.dumps(row), file=log)
    COUNTS[row["phase"]] += 1
    COUNTS[row["phase"] + "_" + row["status"]] += 1


def correctness_case(source, destination):
    with source.open("rb") as disk, destination.open("wb") as sample:
        magic, n, queries = struct.unpack("<8sQQ", disk.read(24))
        if magic != b"ESA2D01\0" or not queries:
            raise ValueError(f"Unexpected disk input: {source}")
        count = min(8, queries)
        sample.write(struct.pack("<8sQQ", magic, n, count))
        remaining = n * 8
        while remaining:
            chunk = disk.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError(f"Truncated disk input: {source}")
            remaining -= len(chunk)
            sample.write(chunk)
        for index in range(count):
            query = index * (queries - 1) // max(1, count - 1)
            disk.seek(24 + n * 8 + query * 24)
            sample.write(disk.read(24))


def check_boundaries():
    max_coord = 2**32 - 1
    path = ROOT / "boundary.bin"
    points = [(0, 0), (0, 0), (max_coord, 0), (0, max_coord), (max_coord, max_coord),
              (max_coord, max_coord), (1, 0), (0, 1), (1, 1), (3, 4), (4, 4)]
    queries = [(0, 0, r) for r in (0, 1, 24, 25, max_coord**2 - 1, max_coord**2,
                                    2 * max_coord**2 - 1, 2 * max_coord**2, 2**128 - 1)]
    queries += [(max_coord, max_coord, 0), (max_coord, max_coord, max_coord**2)]
    rng = random.Random(20261115)
    random_points = [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(1000)]
    queries += [(rng.getrandbits(32), rng.getrandbits(32), rng.getrandbits(64)) for _ in range(50)]
    with (ROOT / "boundary-jobs.jsonl").open("w", buffering=1) as log:
        for sample in ([], points, points + random_points + [(7, 11)] * 200):
            with path.open("wb") as file:
                file.write(struct.pack("<8sQQ", b"ESA2D01\0", len(sample), len(queries)))
                for point in sample:
                    file.write(struct.pack("<II", *point))
                for x, y, r in queries:
                    file.write(struct.pack("<IIQQ", x, y, r & (2**64 - 1), r >> 64))
            for name in ALGORITHMS:
                row = job(name, path, "correctness", case="boundary", n=len(sample))
                record(log, row)
                if row["status"] != "success":
                    raise RuntimeError(f"Boundary test failed: {row}")


def campaign_rows(campaign):
    path = ROOT / campaign / "jobs.jsonl"
    if not path.is_file():
        return []
    with path.open() as log:
        return [json.loads(line) for line in log]


def job_key(row):
    return row["phase"], row.get("geometry","disk"), row["case"], row["algorithm"], row.get("repetition")


def run_campaign(campaign):
    manifest = DATA / campaign / "campaign.json"
    cases = json.loads(manifest.read_text())["cases"]
    paths = {case["id"]: (manifest.parent / case["path"]).resolve() for case in cases}
    status("checking_inputs", campaign=campaign)
    for case in cases:
        if digest(paths[case["id"]]) != (case.get("sha256") or case["conversion"]["sha256"]):
            raise ValueError(f"Input checksum mismatch: {case['id']}")
    theater = "small" if campaign.startswith("2D_ESA_") else "static"
    reference_path = ROOT.parent / campaign / f"indexicon-l2-{theater}-20261105/final/state.json"
    references = defaultdict(set)
    for row in json.loads(reference_path.read_text())["results"]:
        if row["algorithm"] == "indexicon_rtree_point" and row["status"] == "success":
            result = row["result"]
            references[row["case"]].add((result["queries"], result["answers"]))
    if any(len(references[case]) != 1 for case in paths):
        raise ValueError(f"Missing or inconsistent reference counts in {campaign}")

    directory = ROOT / campaign
    directory.mkdir(exist_ok=True)
    sample = min(cases, key=lambda case: case["n"])["id"]
    if not (directory / "correctness.bin").exists():
        correctness_case(paths[sample], directory / "correctness.bin")
    square_source = SQUARE_RUN / campaign
    square_inputs = json.loads((square_source / "inputs.json").read_text())
    square_reference = defaultdict(set)
    with (square_source / "jobs.jsonl").open() as square_log:
        for line in square_log:
            row = json.loads(line)
            if row["algorithm"] == "scan" and row["phase"] == "final" and row["status"] == "success":
                square_reference[row["case"]].add((row["queries"], row["m"]))
    if set(square_inputs) != set(paths) or any(len(square_reference[case]) != 1 for case in paths):
        raise ValueError(f"Missing or inconsistent square inputs or counts in {campaign}")
    previous = {job_key(row):row for row in campaign_rows(campaign)}
    timed_out = {key[1:4] for key,row in previous.items() if key[0]=="final" and row["status"]=="timeout"}
    with (directory / "jobs.jsonl").open("a", buffering=1) as log:
        for name in ALGORITHMS:
            row = previous.get(("correctness","disk",sample,name,None))
            if row is None:
                status("correctness", campaign=campaign, algorithm=name)
                row = job(name, directory / "correctness.bin", "correctness", case=sample)
                record(log, row)
            if row["status"] != "success":
                raise RuntimeError(f"Correctness test failed: {row}")
        for name in SQUARE_EXES:
            row = previous.get(("correctness","square",sample,name,None))
            if row is None:
                row = job(name, square_source / "correctness.bin", "correctness", square=True, geometry="square", case=sample)
                record(log, row)
            if row["status"] != "success":
                raise RuntimeError(f"Square correctness test failed: {row}")
        for phase, reps in (("screen", 1), ("final", 3)):
            jobs = [(case, name, rep, square) for square, roster in ((False, ALGORITHMS), (True, SQUARE_EXES))
                    for case in paths for name in roster for rep in range(reps)]
            random.Random(20261114).shuffle(jobs)
            for number, (case, name, rep, square) in enumerate(jobs, 1):
                geometry = "square" if square else "disk"
                if (phase,geometry,case,name,rep) in previous:
                    continue
                if number == 1 or number % 10 == 0:
                    status(phase, campaign=campaign, job=number, total_jobs=len(jobs))
                key = geometry,case,name
                if phase == "final" and key in timed_out:
                    record(log, dict(phase=phase, geometry=geometry, case=case, algorithm=name,
                                     repetition=rep, status="skipped_after_timeout", wall_seconds=0))
                    continue
                source = square_source / "inputs" / square_inputs[case]["path"] if square else paths[case]
                expected = square_reference[case] if square else references[case]
                row = job(name, source, phase, square=square, case=case, repetition=rep,
                          geometry=geometry)
                if phase == "final" and row["status"] == "timeout":
                    timed_out.add(key)
                if row["status"] == "success" and (row["queries"], row.get("m" if square else "answers")) not in expected:
                    row["status"] = "answer_count_mismatch"
                    row["expected"] = next(iter(expected))
                record(log, row)
    COMPLETE.append(campaign)
    status("campaign_complete", campaign=campaign)


def report():
    ratios = defaultdict(list)
    for campaign in CAMPAIGNS:
        disk, square = defaultdict(list), defaultdict(list)
        reverse = {v:k for k,v in SQUARE_NAMES.items()}
        for base in (SQUARE_RUN, SQUARE_FOLLOWUP, ROOT):
            with (base / campaign / "jobs.jsonl").open() as log:
                for line in log:
                    row = json.loads(line)
                    if row["phase"] != "final" or row["status"] != "success":
                        continue
                    name = reverse.get(row["algorithm"], row["algorithm"])
                    if name not in ALGORITHMS:
                        continue
                    if base == ROOT:
                        target = square if row["geometry"] == "square" else disk
                    elif name not in SQUARE_EXES and row.get("correctness_admission") == "passed":
                        target = square
                    else:
                        continue
                    target[row["case"],name].append(row["query_seconds"])
        for (case, name), rows in disk.items():
            other = square[case,name]
            if len(rows) == len(other) == 3 and min(*rows,*other)>0:
                ratios[name].append(statistics.median(rows)/statistics.median(other))
    write("report.json", {
        "counts": COUNTS,
        "runtime_seconds": time.time() - START,
        "disk_over_square": {
            name: {"matched_cases": len(ratios[name]),
                   "geomean": statistics.geometric_mean(ratios[name]) if ratios[name] else None,
                   "cases_within_30_percent": sum(0.7 < ratio < 1.3 for ratio in ratios[name])}
            for name in ALGORITHMS
        },
    })


def main():
    global START
    os.sched_setaffinity(0, {1})
    spec = dict(campaigns=list(CAMPAIGNS), algorithms=ALGORITHMS, cpu=1, workers=1,
                square_hashes={name: digest(path) for name,path in SQUARE_EXES.items()},
                hashes={exe: digest(ROOT / "bin" / exe) for exe in sorted(set(ALGORITHMS.values()))})
    try:
        if (ROOT / "plan.json").exists():
            if json.loads((ROOT/"plan.json").read_text()) != spec:
                raise RuntimeError("Resume requires identical inputs and binaries")
            previous = json.loads((ROOT/"status.json").read_text())
            if previous["status"] == "complete":
                return
            START = previous["started_unix"]
            COMPLETE.extend(previous["completed"])
            with (ROOT/"boundary-jobs.jsonl").open() as log:
                boundary = [json.loads(line) for line in log]
            if len(boundary)!=3*len(ALGORITHMS) or any(r["status"]!="success" for r in boundary):
                raise RuntimeError("Boundary checks were not completed")
            for row in boundary + [row for name in CAMPAIGNS for row in campaign_rows(name)]:
                COUNTS[row["phase"]] += 1
                COUNTS[row["phase"]+"_"+row["status"]] += 1
            status("resuming")
        else:
            write("plan.json",spec)
            status("checking_boundaries")
            check_boundaries()
        for campaign in CAMPAIGNS:
            if campaign not in COMPLETE:
                run_campaign(campaign)
        report()
        status("complete")
    except Exception as error:
        status("needs_attention", error=str(error))
        raise


if __name__ == "__main__":
    main()
