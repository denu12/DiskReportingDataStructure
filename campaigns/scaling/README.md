# scaling

Static circle reporting as the point count increases. The full campaign has **20 cases**, including five seeds. Both synthetic static campaigns use the same 29-entry competitor roster, including Morton, MortonSIMD and MoronSIMDearly.

The scaling suite varies the point count over 10,000, 100,000, 1,000,000 and 10,000,000. Points are uniform and the radius fraction is 0.01.

Prepare with `python tools/prepare.py --campaign scaling`. Run correctness, screen and final stages with `tools/run.py --campaign scaling`; create the final plan with `tools/plan.py`. All stages sharing a run label share the existing time budgets. `--smoke` prepares explicitly labelled small validation inputs. See the root README for full commands.

Case IDs, seeds and generation parameters are inherited from the former combined `static-circles` campaign. Its historical inputs and results retain their original paths.
