# PostgreSQL Z-ordered range refinement

`postgres_zrange` runs the original Sugiura–Ishikawa PL/pgSQL functions from
[their repository](https://github.com/dbgroup-nagoya-u/psql-refine-z-range), pinned
to `5162f8700a150cdb0dba77159c5cc9b6bbb47a82`. No upstream SQL is modified.
The Python adapter supplies storage, input/output conversion and distance filtering.

## Build and validation

On Linux, install a C compiler, make, bison and flex, then run:

```sh
git submodule update --init src/third_party/psql-refine-z-range
python3 tools/build_postgresql.py
python3 tests/check_postgresql.py
```

The build downloads [PostgreSQL 18.4](https://www.postgresql.org/ftp/source/v18.4/),
checks its pinned SHA-256 and installs under `toolchains/postgresql-18.4`.
`--archive FILE` supports offline builds. `DRR_POSTGRES_HOME` can select another
runtime directory. The source archive, build options and hash are in
`tools/build_postgresql.py`. The benchmark requires NumPy for file loading and
uses libpq directly, with no Python database-driver dependency.

Run the adapter as an ordinary user: PostgreSQL refuses to start as root.
Each job creates its own disposable cluster and private Unix socket, with TCP
listening disabled. It never connects to or alters a system database. Server
processes inherit the benchmark job's CPU affinity and systemd memory limit.
Parallel queries, parallel maintenance, JIT and autovacuum are disabled. The
server uses 256 MiB shared buffers, 64 MiB work memory and 256 MiB maintenance
work memory; durability defaults remain enabled. Shutdown removes the private
cluster after a normal run. A forcibly killed job may leave a disposable
`/tmp/drr-pg-*` directory, but no server survives the benchmark cgroup teardown.

## Query and output contract

Points retain all uint32 coordinates, stored as PostgreSQL `bigint[]`, and a
unique input ID. Duplicate coordinates retain distinct IDs. A generated column
calls the original integer-array `GenZOrderCode`; a PostgreSQL B-tree indexes it.

Upstream refinement permits at most 63 total Morton bits. For dimension `d`,
the adapter uses `b = min(31, floor(63/d))` bits per coordinate. The index cell
for coordinate `x` is `x >> (32-b)`. This is only a coarse index: original points
are never rounded or replaced. The cell width is 2 in 2D and 2048 in 3D.
Dimensions 2 through 63 are supported; larger dimensions are explicitly skipped.

For each ball, the adapter computes an enclosing integer box and maps both
corners to cells. The unchanged `LoosenZOrderRange` enlarges this cell box using
its upstream threshold of 500. The unchanged `RefineZOrderRange` produces its
Morton intervals. A B-tree range join retrieves candidates. An exact SQL
squared-distance test uses `numeric` arithmetic to avoid overflow even at uint32
extremes. The returned IDs are fully materialized in the Python client. This
wrapper tests points from the enlarged cells, so cell quantization does not
change the requested geometric answer.

## Timing and comparison

Construction includes table creation, coordinate serialization and COPY,
generated-key calculation, B-tree construction and ANALYZE. Input-file loading,
private server startup and installation of the original SQL functions are excluded.

Query timing includes computing the box, original loosening and refinement,
B-tree access, exact distance filtering, socket transfer and materializing the
returned IDs. Correctness verification is outside timing. This is an end-to-end
database implementation, so its query cost includes database and client overhead
that standalone C++ indexes do not have. It must not be described as a measurement
of refinement alone. Output records include the PostgreSQL version and key precision;
the harness fingerprints the adapter, SQL functions, server and libpq binaries.

`tests/check_postgresql.py` checks the upstream README example and exact output
multisets in 2D, 3D, 8D, 32D and 63D, including duplicates, empty data, uint32
extremes, disk boundaries and coarse-cell boundaries. It checks both validation
and timed modes, and verifies explicit rejection in 64D.

The static campaign definitions include this entry. Existing prepared manifests
must be regenerated or copied into an explicitly recorded new run; completed
measurements and already running campaign workspaces must not be changed.
The dynamic update-stream adapter is not implemented.

## Temporary-storage cleanup (30 October 2026)

Systemd jobs now receive a separate TMPDIR created before execution and removed
by ExecStopPost after normal exit, timeout, cancellation or process failure.
This covers both the input-format conversion and PostgreSQL cluster files,
including cases where Python finally blocks cannot run. Temporary storage
remains on the same RAM-backed /tmp filesystem. Normal-exit and forced-timeout
cleanup were verified on Archie. The interrupted October 22 PostgreSQL results
are preserved; fresh runs use October 30 labels and do not reuse failed rows.
