# Current native-output Rust dispatcher

This is the canonical driver for Kiddo, Nabo, Neighbourhood, VP-tree, Orthtree,
Grid and SNN Rust. It dispatches dimensions 2–16 and 32. Build it with
`python3 tools/build_native_rust.py` from the repository root; both 2D and
dimensional routing use the resulting isolated executable.

The complete generic search/reporting function is byte-for-byte identical to
the function used by the November 23 repair. Its normalized-text SHA-256 is
`a619b7794bfd4708fac13f0ee9846b1df23c873d1e0ecf0033a90856ce3a228d`.
Only module locations and dimension dispatch changed. Original search modules
remain pinned under the frozen source collection; algorithm behavior and
reporting arithmetic are unchanged.

Superseded duplicate 2D/3D-only bootstrap drivers and the old integer-coordinate
Kiddo/Nabo/Neighbourhood/VP-tree/Orthtree/Grid/SNN adapters were removed. The
separate SPRK targets and their shared driver remain in `dimensional/rust`.
