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
}
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


def job(name, path, phase, **fields):
    cmd = [str(ROOT / "bin" / ALGORITHMS[name]), str(path), name]
    if phase != "correctness":
        cmd.append("--bench")
    row = dict(algorithm=name, phase=phase, **fields)
    start = time.monotonic()
    try:
        process = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=180 if phase == "final" else 60)
        if process.returncode == 0:
            row.update(json.loads(process.stdout))
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
    with (ROOT / "boundary-jobs.jsonl").open("w", buffering=1) as log:
        for sample in ([], points):
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
    directory.mkdir()
    sample = min(cases, key=lambda case: case["n"])["id"]
    correctness_case(paths[sample], directory / "correctness.bin")
    with (directory / "jobs.jsonl").open("w", buffering=1) as log:
        for name in ALGORITHMS:
            status("correctness", campaign=campaign, algorithm=name)
            row = job(name, directory / "correctness.bin", "correctness", case=sample)
            record(log, row)
            if row["status"] != "success":
                raise RuntimeError(f"Correctness test failed: {row}")
        for phase, reps in (("screen", 1), ("final", 3)):
            jobs = [(case, name, rep) for case in paths for name in ALGORITHMS for rep in range(reps)]
            random.Random(20261114).shuffle(jobs)
            for number, (case, name, rep) in enumerate(jobs, 1):
                if number == 1 or number % 10 == 0:
                    status(phase, campaign=campaign, job=number, total_jobs=len(jobs))
                row = job(name, paths[case], phase, case=case, repetition=rep)
                if row["status"] == "success" and (row["queries"], row["answers"]) not in references[case]:
                    row["status"] = "answer_count_mismatch"
                    row["expected"] = next(iter(references[case]))
                record(log, row)
    COMPLETE.append(campaign)
    status("campaign_complete", campaign=campaign)


def report():
    ratios = defaultdict(list)
    for campaign in CAMPAIGNS:
        theater = "small" if campaign.startswith("2D_ESA_") else "static"
        old = defaultdict(list)
        labels = (
            f"additional-{theater}-20261022", f"reporting-adapted-{theater}-20261023",
            "original-all-2d-20261015" if theater == "static" else f"coverage-completion-{theater}-20261030",
        )
        for label in labels:
            path = ROOT.parent / campaign / label / "final/state.json"
            if not path.is_file():
                continue
            for row in json.loads(path.read_text())["results"]:
                if (row["algorithm"] in ALGORITHMS and row["status"] in ("success", "answer_count_mismatch")
                        and row.get("correctness_admission") == "passed" and row.get("cpu") == 1):
                    old[row["case"], row["algorithm"]].append(row["result"])
        new = defaultdict(list)
        with (ROOT / campaign / "jobs.jsonl").open() as log:
            for line in log:
                row = json.loads(line)
                if row["phase"] == "final" and row["status"] == "success":
                    new[row["case"], row["algorithm"]].append(row)
        for (case, name), rows in new.items():
            before = old[case, name]
            if len(before) == len(rows) == 3 and len({(r["queries"], r["answers"]) for r in before + rows}) == 1:
                previous = statistics.median(r["query_seconds"] for r in before)
                current = statistics.median(r["query_seconds"] for r in rows)
                if previous > 0 and current > 0:
                    ratios[name].append(previous / current)
    write("report.json", {
        "counts": COUNTS,
        "runtime_seconds": time.time() - START,
        "query_speedup": {
            name: {"matched_cases": len(values), "geomean": statistics.geometric_mean(values)}
            for name, values in ratios.items() if values
        },
    })


def main():
    os.sched_setaffinity(0, {1})
    with (ROOT / "plan.json").open("x") as plan:
        json.dump(dict(campaigns=CAMPAIGNS, algorithms=ALGORITHMS, cpu=1, workers=1,
                       hashes={exe: digest(ROOT / "bin" / exe) for exe in sorted(set(ALGORITHMS.values()))}), plan, indent=2)
    try:
        status("checking_boundaries")
        check_boundaries()
        for campaign in CAMPAIGNS:
            run_campaign(campaign)
        report()
        status("complete")
    except Exception as error:
        status("needs_attention", error=str(error))
        raise


if __name__ == "__main__":
    main()
