# Owned numeric buffer verification figure

`plot_owned_buffer_bounded13.py` reads the independently reviewed runtime report,
actual stdout, observed group results and original fixed V2 source roster.
It includes all 13 groups from the only admitted invocation: three storage/value
checks, seven move-operation checks, two lifetime/overlap checks and one required
constructor refusal. Each bar reports passing groups over its frozen group
count. The refusal passes only when the original test checks the exact first
`invalid_argument` message. Category membership follows the original source order
and is recorded as exact IDs in figure provenance; no case or failure is omitted.

The renderer never invokes the project executable. Use Python 3.12 and
Matplotlib 3.10.3, a fresh output directory and temporary writable font/cache paths.
From the repository root:

```sh
python tools/phase5_foundation_verification_visuals/plot_owned_buffer_bounded13.py \
  --review reviews/evidence/public_live_affine_v2_foundation_owned_buffer_bounded13_runtime_once_v1_20261009/ROOT_BUFFER_RUNTIME13_REVIEW.json \
  --stdout reviews/evidence/public_live_affine_v2_foundation_owned_buffer_bounded13_runtime_once_v1_20261009/BUFFER_BOUNDED13_STDOUT.txt \
  --results reviews/evidence/public_live_affine_v2_foundation_owned_buffer_bounded13_runtime_once_v1_20261009/BUFFER_BOUNDED13_GROUP_RESULTS.json \
  --roster reviews/evidence/public_live_affine_v2_foundation_owned_numeric_buffer_source_protocol_v2_20261009/FIXED_BUFFER_CASE_ROSTER_AND_SNAPSHOTS_V1.json \
  --output-dir /tmp/owned-buffer-bounded13-figure-reproduction
```

The PNG is 2340 × 1260; the SVG retains editable text. Provenance records exact
source/output hashes, category IDs, dimensions, renderer version, font and color.
Direct labels preserve meaning in grayscale. No timing, RSS or motion is plotted.
Initialized values/moves/public ledgers/lifetimes are tested; private allocator
release order is static source evidence, and real `bad_alloc` cleanup and host-size
overflow remain deferred. The 1024-byte numeric payload bound is not total memory.
Phase5 remains NOT_ACCEPTED and Phase6 NOT_STARTED.
