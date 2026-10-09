"""Persistent experiment-wide budgets, shared by campaigns with the same run label."""
import contextlib
import json
import os
from pathlib import Path
import time


def policy_path(base):
    """A theater run can use a recorded policy without editing repository defaults."""
    return Path(os.environ.get('DRR_EXECUTION_POLICY', base / 'config/execution.json'))


def policy(base):
    return json.loads(policy_path(base).read_text(encoding='utf-8-sig'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


@contextlib.contextmanager
def budget(args):
    import fcntl
    base = args.base.resolve()
    config = policy(base)
    stage = config['stages'][args.phase]
    pool = stage.get('budget_pool', args.phase)
    directory = base / 'results/_budgets'
    directory.mkdir(parents=True, exist_ok=True)
    # One controller at a time, even with different run labels: at most four jobs.
    with (directory / 'controller.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another experiment controller is running in this repository')
        path = directory / (args.run + '.json')
        ledger = json.loads(path.read_text()) if path.exists() else {'stages': {}, 'sessions': []}
        used = ledger['stages'].get(pool, 0)
        remaining = stage['budget_seconds'] - used
        if remaining < stage['timeout_seconds']:
            raise RuntimeError(f'Shared {pool} budget exhausted for run {args.run}')
        start = time.monotonic()
        session = dict(campaign=args.campaign, phase=args.phase, pid=os.getpid(),
                       started_unix=time.time(), reserved_seconds=remaining, status='reserved')
        ledger['sessions'].append(session)
        # Charge the reservation first. An uncatchable crash cannot reset the budget.
        ledger['stages'][pool] = used + remaining
        save(path, ledger)
        args.deadline = start + remaining
        try:
            yield
        finally:
            elapsed = min(remaining, time.monotonic() - start)
            ledger['stages'][pool] = used + elapsed
            session.update(status='closed', charged_seconds=elapsed)
            save(path, ledger)
