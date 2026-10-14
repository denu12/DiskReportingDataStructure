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



def allocation(config, campaign, phase):
    """Protected campaign shares use independent persistent ledger pools."""
    stage = dict(config['stages'][phase])
    pool = stage.get('budget_pool', phase)
    cap = config.get('protected_campaign_budgets', {}).get(campaign, {}).get(phase)
    if cap is not None:
        stage['budget_seconds'] = cap
        pool = phase + ':' + campaign
    return stage, pool


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
    stage, pool = allocation(config, args.campaign, args.phase)
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
        if ':' in pool and pool not in ledger['stages']:
            # Preserve earlier usage when moving a legacy shared ledger to quotas.
            sessions = [s for s in ledger['sessions']
                        if s['campaign'] == args.campaign and s['phase'] == args.phase]
            ledger['stages'][pool] = sum(s.get('charged_seconds', s.get('reserved_seconds', 0))
                                         for s in sessions)
            ledger['protected_campaign_budgets'] = config['protected_campaign_budgets']
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
