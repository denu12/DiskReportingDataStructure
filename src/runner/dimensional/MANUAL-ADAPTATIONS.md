# Manually adapted reporting competitors

The campaign IDs deliberately expose local changes:

* `chan_sss_ddim_MANUALLY_ADAPTED`: Timothy M. Chan's static SSS technique,
  generalized from our existing 2D reporting adaptation. Chan's original code
  is already d-dimensional but solves approximate nearest-neighbour search.
  This adaptation retains its shifted Morton comparator and recursive sorted
  array search. It uses a fixed seed (12121), widened shift arithmetic,
  inclusive bounding-box pruning, a fixed ball radius and exact integer
  membership. Original indices preserve duplicate occurrences.
* `stann_fr_ddim_MANUALLY_ADAPTED`: Michael Connor and Piyush Kumar's STANN,
  using the existing locally modified `init_reporting`/`box_report` traversal.
  The dimensional wrapper instantiates d-dimensional points, carries original
  indices through the sort, and applies exact ball membership to box candidates.
  The existing traversal is reused without further changes. Sorting is serial;
  no OpenMP is enabled.

Neither entry is an unmodified upstream radius-reporting implementation. Both
use full uint32 coordinates and unsigned 128-bit squared distances. The
campaign compares all output indices against an independent brute-force scan;
incorrect outputs, crashes and timeouts are recorded, not repaired.

See the original sources and detailed inherited notices at
`src/third_party/chan_sss/NOTICE.txt` and `src/third_party/stann/NOTICE.txt`.
The upstream files and copyright notices are preserved. No new license is
asserted over either upstream implementation.
