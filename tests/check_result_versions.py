"""Exercise replacement safety with mixed-version benchmark artifacts."""
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import tomllib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import prune_superseded_results as prune
import versioned_results as versioned
import build_native_rust as native
from backends import command
from original_runner import RUST


with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    old=root/'results/campaign/original-all-2d-20261015/final'
    old.mkdir(parents=True)
    job=old/'jobs/old-job';job.mkdir(parents=True)
    (job/'result.json').write_text('{"query_seconds":99}')
    old_row=dict(algorithm='esa_kiddo',case='case',status='success',repetition=0,
                 log='results/campaign/original-all-2d-20261015/final/jobs/old-job/run.log')
    untouched=dict(algorithm='boost_lin',case='case',status='success',repetition=0)
    state=old/'state.json';state.write_text(json.dumps(dict(results=[old_row,untouched])))
    queue=root/'results/_queue-disk-version-repair-20261123';queue.mkdir()
    rows=[dict(campaign='campaign',algorithm='esa_kiddo',case='case',phase='final',
               repetition=i,status='success',query_seconds=1) for i in range(3)]
    log=queue/'jobs.jsonl'
    log.write_text('\n'.join(json.dumps(r) for r in rows[:2]))
    selected=prune.replacements(None,[queue])
    assert not selected,'Two new repeats must not delete a complete old version'
    log.write_text('\n'.join(json.dumps(r) for r in rows))
    selected=prune.replacements(None,[queue])
    assert len(selected)==1
    prune.live(root/'results',selected,True)
    assert json.loads(state.read_text())['results']==[untouched]
    assert not job.exists(),'Superseded per-job timing must be deleted as well'
    assert log.exists(),'The replacement must remain intact'
    # A timeout replaces an older version without inventing a numeric score.
    log.write_text(json.dumps(dict(rows[0],phase='screen',status='timeout')))
    assert len(prune.replacements(None,[queue]))==1
    # A backend error is not a usable replacement and cannot erase old data.
    log.write_text(json.dumps(dict(rows[0],phase='screen',status='error')))
    assert not prune.replacements(None,[queue])

    source=ROOT/'src/runner/native-rust/main.rs'
    identity=native.prepare(source,root/'driver',ROOT)
    assert identity['dimensions']==tuple(range(2,17))+(32,)
    assert identity['algorithm_changes'] is False
    assert identity['generic_run_sha256']=='a619b7794bfd4708fac13f0ee9846b1df23c873d1e0ecf0033a90856ce3a228d'
    before=source.read_text();after=(root/'driver/main.rs').read_text()
    assert before[before.index('fn run<'):before.index('fn main()')]==after[after.index('fn run<'):after.index('fn main()')]

for algorithm in RUST:
    route=command(algorithm)
    assert route[1]==str(ROOT/'tools/original_runner.py'),(algorithm,route)
manifest=ROOT/'src/runner/dimensional/rust/Cargo.toml'
targets=tomllib.loads(manifest.read_text())['bin']
assert {x['name'] for x in targets}=={'ddim-sprk-ids-check','sprk-adapted-3d-check'}
for target in targets:assert (manifest.parent/target['path']).is_file(),target
print('Passed replacement safety, timeout/error policy, unchanged native search, routing and retained-target checks')
