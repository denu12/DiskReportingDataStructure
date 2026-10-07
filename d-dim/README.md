# D-dimensional competitor adapters

This folder contains the agreed higher-dimensional competitors and their input/output adapters. Our publication implementations are exclusively the three 2D files `Morton.cc`, `MortonSIMD.cc` and `MoronSIMDearly.cc` under `src/app/algorithms/sfc`; no additional Morton implementation is shipped here.

The dimensional roster has 20 entries, including a brute-force control. Chan and STANN reporting adaptations retain their explicit `MANUALLY_ADAPTED` names. See [manual adaptations](MANUAL-ADAPTATIONS.md), [adapter details](ESA-ADAPTERS.md), and the [ESA campaign guide](../campaigns/ESA.md).

Build on Arch with `python tools/build_ddim.py`. The CMake target `ddim_check` handles the manually adapted Chan and STANN competitors; the build script also builds the foreign and Rust adapters. Third-party credits and licensing notices remain in the repository.
