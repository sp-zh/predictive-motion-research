# Recorded task videos

See [the showcase](../docs/showcase.md) for three curated Phase 4 task-completion
clips. MP4s use H.264, 1280×720, 30 fps and 1x simulated-time playback. Each has
start/middle/end thumbnails and a JSON identity/provenance record.

These are renders of original measured `q_post` records, using MuJoCo forward
geometry without new controller execution or dynamics integration. Position
error and model clearance annotations come from the original audited CSVs.
The clips are selected successful diagnostics, not complete method comparisons.

Reproduction requires the local raw evidence, MuJoCo 3.3.7, NumPy, Pillow,
ffmpeg, pinned FR3 assets under `.vendor/menagerie/`, and the scene produced by
`python3 cad/scripts/assemble_scene.py`. On macOS the rendering process needs
access to the system graphics service. Run from the project root, for example:

```sh
python3 scripts/render_task_video.py \
  --csv results/phase4-export/predictive_motion/results/phase4/raw/frozen-v4/evaluation/reactive_qp_81011.csv \
  --summary results/phase4-export/predictive_motion/results/phase4/frozen-v4/evaluation/reactive_qp_81011.yaml \
  --scene experiments/generated/inspection/scene.xml \
  --output videos/new-reactive-qp-replay.mp4 \
  --title 'Reactive QP | constrained inspection completed'
```

The renderer refuses to overwrite a published MP4 and verifies pinned assets
and matching frozen CAD/reference inputs. The videos have no audio. Rendering
on another platform is not expected to produce a byte-identical encoder output;
input identities and measured trajectory remain the reference.
