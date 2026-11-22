"""Isolate failing benchmark pairs and suppress retries after a timeout."""
import threading
import time

ERRORS = {'error', 'crash', 'memory', 'oom', 'infrastructure_error', 'unsupported_input'}


class PairPolicy:
    def __init__(self, rows=()):
        self.guard = threading.RLock()
        self.locks = {}
        self.failed = {}
        for row in rows:
            self.observe(row)

    def lock_for(self, algorithm, case):
        with self.guard:
            return self.locks.setdefault((algorithm, case), threading.RLock())

    def skip_status(self, algorithm, case):
        with self.guard:
            return self.failed.get((algorithm, case))

    def observe(self, row):
        outcome = row['status']
        skip = ('skipped_after_timeout' if outcome in {'timeout', 'skipped_after_timeout'} else
                'skipped_after_error' if outcome in ERRORS | {'skipped_after_error'} else None)
        if skip:
            with self.guard:
                self.failed[(row['algorithm'], row['case'])] = skip

    def execute(self, algorithm, case, repetition, call):
        with self.lock_for(algorithm, case):
            start = time.monotonic()
            skip = self.skip_status(algorithm, case)
            if skip:
                return dict(algorithm=algorithm, case=case, repetition=repetition,
                            status=skip, wall_seconds=0)
            try:
                row = call()
            except Exception as error:
                row = dict(algorithm=algorithm, case=case, repetition=repetition,
                           status='error', detail=f'{type(error).__name__}: {error}',
                           wall_seconds=time.monotonic()-start)
            self.observe(row)
            return row
