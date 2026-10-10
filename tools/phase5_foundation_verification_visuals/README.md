# Finite foundation verification figure

`plot_bounded66.py` reads an independently accepted review, actual stdout and
the original case roster. It renders all 66 grouped checks, including required
refusals. It never invokes the test executable, Model or controller.

The verified renderer uses Python 3.12 and Matplotlib 3.10.3. Python 3.14 with
that Matplotlib release failed during tick construction; the rendering failure
and an earlier spacing revision are retained in the milestone's excluded
archive. Temporary environments and font caches are excluded from Git.

From the repository root, with that renderer available:

```sh
python tools/phase5_foundation_verification_visuals/plot_bounded66.py \
  --review reviews/evidence/public_live_affine_v2_foundation_bounded66_runtime_once_v1_20261009/ROOT_BOUNDED66_RUNTIME_REVIEW.json \
  --stdout reviews/evidence/public_live_affine_v2_foundation_bounded66_runtime_once_v1_20261009/FOUNDATION_BOUNDED66_STDOUT.txt \
  --roster reviews/evidence/public_live_affine_v2_foundation_mesh_ledger_source_protocol_v1_20261009/FIXED_CASE_ROSTER_V1.json \
  --output-dir /tmp/foundation-bounded66-figure-reproduction
```

Use a fresh output directory and writable temporary `MPLCONFIGDIR` and
`XDG_CACHE_HOME` if the renderer cannot use its default font caches.
PNG, editable SVG and provenance record the source hashes, counts, renderer
version, font, dimensions, color and artifact hashes. SVG identifiers use a
fixed salt and the export omits a changing creation timestamp.

The axis counts groups, not individual assertions, trajectories or code
coverage. No timings are plotted. Passing this finite roster does not accept
Phase 5 or establish motion, controller performance or physical memory bounds.
