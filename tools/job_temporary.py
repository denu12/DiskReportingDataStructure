"""Give each systemd benchmark job temporary storage with stop-time cleanup."""
import re

def properties(unit):
    if not re.fullmatch(r"(?:esa2d|esa-family|drr-cleanup-test)-[A-Za-z0-9-]+", unit):
        raise ValueError("Unexpected benchmark unit name")
    path = "/tmp/drr-job-" + unit
    return ["-p", "ExecStartPre=/usr/bin/mkdir -m 700 -- " + path,
            "-p", "Environment=TMPDIR=" + path,
            "-p", "ExecStopPost=/usr/bin/rm -rf -- " + path]
