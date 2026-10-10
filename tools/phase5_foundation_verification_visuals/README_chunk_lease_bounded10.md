# Chunk IO lease verification figure

`plot_chunk_lease_bounded10.py` reads the independent runtime review, actual stdout,
observed group results and the original fixed lease source roster. It includes all
ten groups from the only admitted invocation, in source order: one healthy
open/reopen group, three reentry/poison/reset groups, two case/batch isolation
groups and four move/lifetime groups. Each bar reports passing groups over its
frozen group count. Nested expected refusals are checked within their groups and
are not counted as additional experiments or failures. Exact group IDs and the
1/3/2/4 partition are recorded in figure provenance.

The renderer never invokes the project executable. Use Python 3.12 and
Matplotlib 3.10.3, a fresh output directory and temporary writable font/cache paths.
From the repository root:

```sh
python tools/phase5_foundation_verification_visuals/plot_chunk_lease_bounded10.py \
  --review reviews/evidence/public_live_affine_v2_foundation_chunk_io_lease_bounded10_runtime_once_v1_20261009/ROOT_LEASE_RUNTIME10_REVIEW.json \
  --stdout reviews/evidence/public_live_affine_v2_foundation_chunk_io_lease_bounded10_runtime_once_v1_20261009/LEASE_BOUNDED10_STDOUT.txt \
  --results reviews/evidence/public_live_affine_v2_foundation_chunk_io_lease_bounded10_runtime_once_v1_20261009/LEASE_BOUNDED10_GROUP_RESULTS.json \
  --roster reviews/evidence/public_live_affine_v2_foundation_chunk_io_lease_source_protocol_v1_20261009/FIXED_LEASE_ROSTER_AND_PUBLIC_STEPS_V1.json \
  --output-dir /tmp/chunk-lease-bounded10-figure-reproduction
```

The PNG is 2340 × 1260; the SVG retains editable text. Provenance records exact
source/output hashes, category IDs, dimensions, renderer version, font and color.
Direct labels preserve meaning in grayscale. No timing, RSS or motion is plotted.
The ten groups validate finite public lease behavior and zero accounting; they do
not validate actual file/stream IO, thread safety, private active state, capture,
allocator behavior or full loader/OS closure. Four type-contract assertions passed
in an earlier compilation and are not extra runtime groups. The 204 source
observation fragments are not a measured dynamic call count. Phase5 remains
NOT_ACCEPTED and Phase6 NOT_STARTED.
