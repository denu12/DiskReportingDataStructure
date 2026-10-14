# radius_scaling

Part of the [2D static theater](../../README.md). **35 instances**: four million uniform uint32 points, seven fixed radii, five seeds, and 1,000 queries per instance.

| Nominal interior answers | Radius / grid width |
|---:|---:|
| 1 | 0.000282094792 |
| 10 | 0.000892062058 |
| 100 | 0.00282094792 |
| 1,000 | 0.00892062058 |
| 10,000 | 0.0282094792 |
| 100,000 | 0.0892062058 |
| 1,000,000 | 0.282094792 |

Radii follow the volume of a 2D Euclidean ball. These answer counts are design values, not guarantees: queries near the cube boundary return fewer points. The integer radius is rounded once and squared exactly. Actual returned counts are recorded.

Each seed uses identical indexed points and query centers across all seven radii. This isolates radius scaling from changes in the dataset or query locations. No pilot calibration is used. The companion [input_scaling](../input_scaling/README.md) campaign varies input size while targeting 1,000 answers.

The [campaign.json](campaign.json) defines the workload. Its execution ID is `radius_scaling`. Prepared files live in `data/radius_scaling/`; results live in `results/radius_scaling/<run>/<phase>/`. It uses the theater's existing roster, timing contract and resource policy.

Prepare with `python tools/prepare.py --campaign radius_scaling`. Preview with `python run_theater.py static`; execution requires a fresh run label and `--execute`.
