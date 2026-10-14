# radius_scaling

Part of the [3D static theater](../../README.md). **35 instances**: four million uniform uint32 points, seven fixed radii, five seeds, and 1,000 queries per instance.

| Nominal interior answers | Radius / grid width |
|---:|---:|
| 1 | 0.00390796321 |
| 10 | 0.0084194515 |
| 100 | 0.0181391584 |
| 1,000 | 0.0390796321 |
| 10,000 | 0.084194515 |
| 100,000 | 0.181391584 |
| 1,000,000 | 0.390796321 |

Radii follow the volume of a 3D Euclidean ball. These answer counts are design values, not guarantees: queries near the cube boundary return fewer points. The integer radius is rounded once and squared exactly. Actual returned counts are recorded.

Each seed uses identical indexed points and query centers across all seven radii. This isolates radius scaling from changes in the dataset or query locations. No pilot calibration is used. The companion [input_scaling](../input_scaling/README.md) campaign varies input size while targeting 1,000 answers.

The [campaign.json](campaign.json) defines the workload. Its execution ID is `radius_scaling_3d`. Prepared files live in `data/radius_scaling_3d/`; results live in `results/radius_scaling_3d/<run>/<phase>/`. It uses the theater's existing roster, timing contract and resource policy.

Prepare with `python tools/prepare_synthetic_ddim.py --campaign radius_scaling_3d`. Preview with `python run_theater.py static-3d`; execution requires a fresh run label and `--execute`.
