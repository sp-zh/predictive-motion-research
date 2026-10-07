# CAD source and export review

Decision: **PASS for reproducible geometry generation and export**. This is not acceptance of the integrated inspection benchmark, robot reachability or collision-query fidelity.

## Evidence

`cad/scripts/run_cad.sh` executed on Dell Ubuntu 24.04 with official FreeCAD 1.1.4 (upstream commit `4fd3bf320d9566a27e60069fc8387448aaa3a094`). Its 820,812,280-byte AppImage passed the SHA-256 check in `scripts/fetch_freecad.sh`. The archive is on D-drive storage and the extracted executable runs on native Linux storage.

The tool has a four-hole adapter, 0.30 m shaft, parameterized sensor body, spherical tip, TCP offset and optional bracket. The fixture has a base, narrow 0.075 m channel, two walls and rear guard. Sources include the parameter JSON, FeaturePython proxy code, saved FCStd, STEP, visual STL and simplified collision STL. Generated files are actual CAD exports, not hand-authored placeholder meshes.

The visual tool has 3,564 triangles; its collision model has 904 triangles with bolt holes filled. The fixture uses 48 triangles. Mesh bounds are recorded in metres in `cad/generated/cad_evidence.json`. STEP dimensions are millimetres. A separate process restored both saved Python proxies, changed shaft length by 20 mm, observed changed geometry, read valid STEP solids and checked mesh/STEP scale. All checks passed in `persistence_evidence.json`.

## Known issues, debt and scientific risks

- The export line remains a geometry placeholder. A separate 3D curve with defined orientation passed 81 discrete offline poses; continuous feasibility, scenario families and executed controller comparisons remain pending.
- Adapter dimensions are experimental, not a certified physical FR3 mounting interface. Hardware fabrication/motion is outside scope.
- A single convex hull of the fixture would fill its channel. Collision integration must preserve individual components and validate distances/contact truth before constrained benchmarks.
- Compound CAD volumes may include intersecting component volumes; do not treat their sum as calibrated physical mass.
- FCStd and STEP packaging/timestamps can change across regeneration. Per-run hashes establish transfer identity; geometry tests establish dimensional reproducibility.
- Fresh-process parametric editing requires the project proxy module on FreeCAD's Python path. The supplied runner supplies it.

No geometry-only evidence closes the collision validation or research scenario gates.

## Scene integration follow-up

The CAD was attached to the upstream FR3 flange in generated MJCF. A C++ probe checked the physical TCP site against the validated kinematics at 64 random configurations (seed 913), with maximum position mismatch 1.494e-15 m and rotation mismatch 1.635e-15 rad. Cylinder dimensions and the preserved 0.075 m fixture channel match source parameters. The payload's 0.45 kg mass, COM and principal inertia are declared simulation assumptions.

The original x=0.40 m fixture caused two contacts and minimum tool/fixture distance -0.008023 m during held home simulation; this initialization correctly failed. Its source parameters and evidence are preserved in `results/cad/initial_*`. Moving the fixture to x=0.70 m before any comparative trials produced zero contacts and minimum separation 0.13056 m over 1,000 held steps / 4 simulated seconds. `scene_evidence.json` and `render.log` record the successful startup check and actual 800x600 OpenGL render. These results validate startup and scene plumbing, not a motion-planning or collision-control benchmark.

## Independent distance and path follow-up

The full-tool startup gate now requires conservative world-AABB separation, with minimum lower bound 0.122684 m and zero contacts. Native distance is diagnostic only after a 2,592-query independent bound check found 4 native and 356 legacy violations. A separate 81-pose 3D curve passed with minimum full-tool lower bound 0.01549999718 m, position error <=8.2764e-7 m and rotation error <=1.3088e-6 rad. These discrete results do not close continuous collision or controller gates. Details and retained failures are in `docs/collision_query_diagnostic.md`.

## Post-step observation alignment

The startup probe now copies the post-step state into independent mjData and runs mj_forward there. All 1,000 observation calls left the original mjSTATE_INTEGRATION vector unchanged and matched q/time; maximum post-step TCP/FK discrepancy is 1.290e-15 m and 1.662e-15 rad. The synchronized conservative lower bound is 0.1226841945 m and zero contacts; native diagnostic minimum is 0.1305615509 m. Historical unsynchronized records remain preserved.
