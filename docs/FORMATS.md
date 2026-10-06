# Workload format

All integers are little-endian. Coordinates are uint32. Closed circles have `(x, y, squared_radius_low64, squared_radius_high64)`, with an unsigned 128-bit squared-radius threshold.

Static/ESA: eight-byte magic `ESA2D01\0`, uint64 point count, uint64 query count, points (two uint32), then circles (two uint32 and two uint64).

Dynamic: eight-byte magic `DRRDYN1\0`, uint64 initial-point count, uint64 operation count, initial points, then operations. An operation is a uint8 kind followed by a circle record. Kinds: 0 insert, 1 delete one occurrence, 2 query. Radius fields are zero for updates. Generators guarantee valid deletions.

Generated JSON manifests describe cases, hashes, seeds, geometry, algorithms and resource policy. Results record status, separate build/query/update seconds, operation counts and answer counts. `tools/collect.py` emits CSV without inventing timings for failures.
