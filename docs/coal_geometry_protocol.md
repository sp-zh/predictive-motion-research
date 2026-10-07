# Independent primitive query protocol

The offline `coal_query_probe` is a CAD geometry audit. It links the installed Coal 3.0.3 C++ API and uses signed distances with GJK/EPA tolerances 1e-10 and 256 GJK iterations. It does not implement the controller collision adapter.

Analytic cases use fixed seed 5021 and include sphere/sphere separation and penetration, rotated box/sphere separation, common-orientation box/box separation and penetration, and cylinder/sphere radial separation and penetration. Independent formulas supply signed distance and expected normal. Gates are 1e-7 m distance, witness-vector and swapped-order distance error, and 1e-6 normal error. The witness convention is `p_fixture - p_tool = distance * normal`.

For scene cases, all five tool primitives and four fixture components are tested at each pose. Initial tool geometry transforms are imported from the assembled model only to verify the CAD integration; subsequent poses and Jacobians are computed from Pinocchio. Their transforms are independently compared against the MuJoCo plant, with 1e-9 tolerance. This offline model import must not be copied into the controller runtime; its geometry must come from the explicit CAD/robot collision configuration.

For a fixed fixture and a tool witness point p, the analytic derivative is

`dd/dq = -normal^T [Jv_TCP + Jw_TCP × (p - p_TCP)]`.

The Jacobian is LOCAL_WORLD_ALIGNED, ordered linear then angular. Central finite differences use h=1e-6 rad, with a predeclared 2e-4 m/rad gate. The two one-sided slopes and the interval containing the selected witness derivative are recorded separately to diagnose closest-feature changes. A single selected nearest point need not define a classical derivative when several points are equally close.

The original fixed-orientation inspection curve intentionally remains unchanged. Its derivative audit failed 1,018 of 1,620 pair cases; the same 1,018 have one-sided slope gaps above 5e-4 m/rad, maximum gap 0.21063 m/rad. The selected witness derivative remains within the one-sided slope interval to 7.88e-5 m/rad. Distance and witness checks pass. These observations support closest-feature nonsmoothness and must not be relabeled as a passing differentiable-distance gate.

An independent diagnostic perturbs each recorded q by uniform +/-0.005 rad using Python Random seed 5022. It is a geometry test, not a changed benchmark or trajectory. All 1,620 perturbed pairs passed; maximum derivative error was 3.72721e-5 m/rad. The exact perturbations and metadata are retained. That test establishes the derivative convention on these smooth poses; it does not resolve the original path's nonsmooth constraints, continuous safety, mesh conservatism or robot self-collision.

Compile and run on Dell:

```sh
source /opt/ros/jazzy/setup.bash
source install/setup.bash
cmake -S tests/integration/inspection_scene -B build/inspection_scene
cmake --build build/inspection_scene --target coal_query_probe --parallel 2
build/inspection_scene/coal_query_probe experiments/generated/inspection/scene.xml \
  src/predictive_motion_kinematics/config/fr3.yaml \
  results/cad/path_screening_aabb/feasible_path.csv results/cad/fresh_path_audit
```

The last command returns failure for the recorded nonsmooth derivative cases; use a fresh output directory to preserve prior evidence. Replacing the pose CSV with `results/cad/coal_jitter_poses.csv` runs the perturbation diagnostic. Never remove offending pairs or tune tolerances based on held-out controller results.

Coal's documented [DistanceResult](https://docs.ros.org/en/jazzy/p/coal/generated/structcoal_1_1DistanceResult.html) provides signed distances, witness points and normals. Numerical evidence above comes from this project's executable audit. Original failures, signed-case follow-up and source snapshots are retained under `results/cad/coal_*`.
