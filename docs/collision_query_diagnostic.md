# Collision-query diagnostic and offline path scope

MuJoCo 3.3.7 distance queries are not accepted as the controller's constraint provider. The independent C++ probe in `tests/integration/inspection_scene/distance_query_probe.cpp` evaluates the optional camera bracket against all four fixture components at 81 recorded poses, with native CCD enabled/disabled and four query caps (10, 1, 0.1, 0.03 m).

For each pair, the probe transforms the enclosing local primitive boxes into enclosing world axis-aligned boxes. The Euclidean norm of positive axis separation is a conservative lower bound on shape separation. A query returning less than `min(query_cap, box_lower_bound)` beyond numerical tolerance contradicts that bound. Intersecting boxes give zero and establish no clearance.

| Mode | Queries | Bound violations |
|---|---:|---:|
| Native CCD | 1,296 | 4 |
| Legacy fallback | 1,296 | 356 |

With native CCD and caps of 10 or 1 m, sample 10 reports zero bracket/right-wall distance despite a 0.2280000005 m box separation lower bound. Sample 41 similarly reports zero despite a 0.1504999983 m lower bound. Native smaller caps had no violations in this dataset; this does not validate those caps generally. Switching to the legacy algorithm increased violations. Raw rows, configurations, query caps and world bracket centers are preserved in `results/cad/distance_query_diagnostic.csv`.

The pinned [MuJoCo 3.3.7 distance-query implementation](https://github.com/google-deepmind/mujoco/blob/3.3.7/src/engine/engine_support.c) selects native CCD for supported convex pairs and otherwise uses collision functions with a margin. This source explains the two diagnostic modes; the discrepancy above comes from our recorded numerical experiment.

## Accepted evidence and remaining gates

`results/cad/path_screening_aabb` uses conservative box separation for every tool component, including the optional bracket, and all four fixture parts. Its 81 discrete IK poses passed: minimum lower bound 0.01549999718 m, maximum TCP position error 8.2764e-7 m and maximum rotation error 1.3088e-6 rad. The curve has 0.20 m forward travel, 7 mm lateral and 10 mm vertical excursions, with the shaft pointing along world +X. These are offline poses, not executed controller trials or a continuous collision certificate.

Earlier `path_screening` omitted the bracket and retains an explicit scope correction. `path_screening_final` includes it but fails the raw native-distance gate; those failures remain preserved. No component was removed to make the final check pass. Held startup now uses the full-tool conservative bound (minimum 0.122684 m), retaining the synchronized native reported 0.130562 m as a diagnostic, and records zero contacts over 1,000 steps / 4 simulated seconds. Scratch-data observation refresh leaves integration state byte-identical; post-step TCP/FK discrepancies are <=1.29e-15 m and <=1.67e-15 rad. The earlier unsynchronized native value was 0.130556 m.

Before Phase 4 constrained-control acceptance, independently validate Coal/FCL distances, nearest-point ordering, normals, finite-difference distance Jacobians, representation conservatism and contact correspondence. Box bounds can screen separated offline poses but do not supply the differentiable constraints required for the research controller. Continuous motion, robot self-collision, intermediate samples, scenario families and held-out executed comparisons remain open.
