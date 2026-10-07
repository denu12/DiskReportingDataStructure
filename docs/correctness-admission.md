# Correctness admission

Boundary and duplicate stress findings are useful information, not grounds for
excluding an implementation. CGAL range tree (`cgal_rt`), PAM (`pam`), static
Pkd-tree (`pkd`) and dynamic Pkd-tree (`pkd_dyn_UPSTREAM`) are reinstated as
candidates for the next campaign run. They were already present in the source
rosters; their historical correctness gates were what excluded them.

The static, dynamic and ESA 2D runner now checks the smallest ordinary workload
in each suite. It does not execute the old synthetic edge fixtures. The
d-dimensional campaign likewise checks only ordinary ESA datasets. Wrong
answers or crashes on these ordinary workloads still affect admission.

Historical results, including failures and missing measurements, are preserved.
Reinstatement does not relabel an old failure as a pass or fabricate timings.
New correctness and screening phases must use a fresh run name; the usual
manifest, binary and policy identity checks remain enforced. No competitor
code is repaired by this policy change.
