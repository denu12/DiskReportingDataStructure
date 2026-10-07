# static

Static circle reporting at a fixed point count. The full campaign has **30 cases**, including five seeds. Both synthetic static campaigns use the same 29-entry competitor roster, including Morton, MortonSIMD and MoronSIMDearly.

Every full-size case uses 1,000,000 points. The distributions suite compares uniform, normal and skewed points (15 cases); the selectivity suite varies the radius fraction over 0.001, 0.01 and 0.1 (15 cases).

Prepare with `python tools/prepare.py --campaign static`. Run correctness, screen and final stages with `tools/run.py --campaign static`; create the final plan with `tools/plan.py`. All stages sharing a run label share the existing time budgets. `--smoke` prepares explicitly labelled small validation inputs. See the root README for full commands.

Case IDs, seeds and generation parameters are inherited from the former combined `static-circles` campaign. Its historical inputs and results retain their original paths.
