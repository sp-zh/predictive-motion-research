# Parametric inspection assembly

On the Dell Linux workspace, run:

```sh
PM_CACHE=/mnt/d/CodexTransfer/projects/predictive_motion/cache bash scripts/fetch_freecad.sh
bash cad/scripts/run_cad.sh
```

The official FreeCAD 1.1.4 x86-64 AppImage is hash pinned. Its extracted runtime runs from the native Linux filesystem; its 783 MiB archive may stay on the D-drive cache. No system installation or root access is needed.

Edit `source/inspection.json`, expressed in metres. The generator creates typed FreeCAD parameters, source `.FCStd`, STEP in millimetres, visual and simplified collision STL in metres, and an initial inspection line. A separate process opens the saved document, restores Python proxies, changes shaft length, recomputes, reads STEP and checks mesh scale. Keep `cad/scripts` on the FreeCAD Python path when opening the document to edit its parametric features.

The flange adapter bolt pattern is an experimental CAD parameter, not a certified manufacturing interface. The export's initial straight line is a geometry placeholder. A separate three-dimensional curve with defined orientation passed 81 discrete pose checks in `benchmarks/reference/inspection_curve.json`; continuous motion and controller trials remain pending. Fixture walls must be loaded as separate collision primitives or components: taking a single convex hull of the compound fixture would incorrectly fill its narrow channel. The tool collision adapter fills its bolt holes conservatively; future controller collision tests must compare the chosen representation against these source solids.

Generated files and their hashes are in `generated/cad_evidence.json`; fresh-process checks are in `generated/persistence_evidence.json`. STEP export timestamps and FCStd packaging can vary between regenerations, so compare geometry and recorded source parameters in addition to per-run file hashes.

## Robot scene integration

`bash scripts/verify_inspection_scene.sh` assembles the pinned arm and CAD exports, builds a C++ probe and checks 64 random TCP transforms, primitive scale/channel dimensions and 1,000 held simulation steps. `source/simulation.json` declares a 0.45 kg payload and inertia as simulation assumptions, not measured physical properties. The robot's original joint dynamics/actuators remain upstream; the original caches are never edited. Collision primitives remain separate, preserving the fixture channel.

The first fixture origin x=0.40 m produced an 8.02 mm initial penetration. It is retained in `results/cad/initial_*` as a failed startup check. Before freezing any benchmark, the origin was moved to x=0.70 m: the held home pose has zero contacts and a 0.122684 m conservative full-tool clearance lower bound. The synchronized native 0.130562 m distance is retained only as a diagnostic. Scratch-data observation refresh is verified not to change integration state and matches post-step FK. See [distance-query validation and path scope](../docs/collision_query_diagnostic.md). These checks do not establish continuous collision avoidance during motion. Generated scene XML has host-local asset paths and is regenerated from source instead of committed.
