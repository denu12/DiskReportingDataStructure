"""Apply portable per-process limits before exec (no threaded preexec_fn)."""
import os,resource,sys
cpu,memory,timeout=map(int,sys.argv[1:4])
os.sched_setaffinity(0,{cpu})
resource.setrlimit(resource.RLIMIT_AS,(memory,memory))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
resource.setrlimit(resource.RLIMIT_CPU,(timeout,timeout+1))
os.execvpe(sys.argv[4],sys.argv[4:],os.environ)
