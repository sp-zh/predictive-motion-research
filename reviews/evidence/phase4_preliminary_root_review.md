# Preliminary Phase 4 root checks

Historical preliminary review, superseded by the scoped PASS in `reviews/phase_4_review.md`. The statements below record the state before final package review.

Formal gate remains pending the immutable source/evidence export and regression evidence. This file records completed independent checks, not a phase PASS.

The root-written `scripts/phase4/audit_root_csv.py` ran on Dell Python/NumPy, without production Pinocchio/IK/QP calls. Its exact source SHA-256 is `1bf218a7656397d4d0ae54354043f47e23ed139154564c9bfff961219c2a2f1f`. `results/phase4-early-review/root-csv-audit-20261005.json` records PASS for 20 expected diagnostic trials and 185,151 rows: physical/command bounds, numerical tolerances, derivatives, accepted target integration, state age, no-command termination records and summary/failure consistency. There are 7,430 independent URDF SE(3) residual checks, maximum translation-residual error 1.077e-15 and rotation error 9.676e-16.

The executed outcomes are 15 completions, four Servo singularity halts and one evaluation QP infeasible-bounds termination. The failures remain in the roster. These two evaluation seed clusters are component diagnostics and do not support general comparative research claims.

The source read found the online physical safety monitor missing measured joint-position checks; retrospective CSV checks do pass but cannot replace that monitor. The executor was asked to add a separate regression/fix identity while preserving frozen-v4 traces. Decision-age timing excludes command commit and following physics/observation/logging, so no complete-cycle 4ms guarantee is established. Baselines are supervised constrained projections and must retain that label. Generated Servo URDF/SRDF, meshes and input-library closure need explicit export identities; post-run hashes must not be relabeled pre-run freezes.

Recorded contact counts use independent scratch full-forward observations at each 2ms physics sample. This review does not establish contact forces/efforts, continuous intersample collision certificates or real-time hardware safety. Geometry derivative/enclosure, actual Servo and solver/failure-consumer checks await the final evidence package.
