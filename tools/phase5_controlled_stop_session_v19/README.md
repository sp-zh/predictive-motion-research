# Interior first-command planning repair66

This version keeps the original strict command checks and solves a narrower planning problem: only the seven existing extra first-command intervals move inward. An explicit affine blend of the genuine nominal and old interval midpoint supplies seven optimizer-starting coordinates. It never clips a solver return, actual state or accepted command.

The exact101-file main-build source is stored as five overrides and96 unchanged files in immutable V18. Every name, byte length and SHA is pinned in `EFFECTIVE_SOURCE_MANIFEST.json`. Run `python3 materialize_source.py --check` to verify it without writing. Supply a fresh absolute output directory instead of `--check` to restore the exact flat source tree before building.

The frozen `contract_interior66_tests.cpp` preserves the initial failed test, which incorrectly expected a ray diagnostic table even when the original initializer accepted an already feasible seed. `regression2/contract_interior66_tests.cpp` is the separately compiled correction: all7337 row values,126 unchanged non-beta coordinates,134 bounded hint events and all original strict checks pass. The main compiler input set was not edited after building.

Saved-data native regression reproduces the original65 refusal and passes original14756SI/strict200/400 command-history arithmetic after the repair. These checks do not establish nonlinear B400, physical stopping, timing, a complete task, hardware safety or research acceptance. Phase5 remains NOT_ACCEPTED; Phase6 NOT_STARTED. Source and archive qualification precede any separate fresh66 entry.
