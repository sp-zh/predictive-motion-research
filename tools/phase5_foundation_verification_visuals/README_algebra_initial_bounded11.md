# Initial-state contract verification figure

The two panels show different grains: eleven original test groups and 97 entries at the compiled validator callsite. They partition all admitted cases, including five accepted finite inputs and 92 required exceptions. No successful subset was selected. Counts do not represent independent experiments, all C++/native/getter calls, robot motion or controller performance. Phase5 remains NOT_ACCEPTED.

The renderer requires the independent Root review, exact actual stdout, original pre-run roster and observed group results. It checks their identities and count closure before plotting. The PNG is 2340 × 1260; the editable SVG and source/data hashes are recorded in figure provenance. Both axes start at zero. Color and grayscale exports were inspected for clipping, overlap and label readability.

Run from the repository root with the existing Matplotlib environment:

```sh
python tools/phase5_foundation_verification_visuals/plot_algebra_initial_bounded11.py \
  --review reviews/evidence/public_live_affine_v2_foundation_algebra_initial_bounded11_runtime_once_v1_20261009/ROOT_INITIAL_RUNTIME11_REVIEW.json \
  --stdout reviews/evidence/public_live_affine_v2_foundation_algebra_initial_bounded11_runtime_once_v1_20261009/INITIAL_BOUNDED11_STDOUT.txt \
  --roster reviews/evidence/public_live_affine_v2_foundation_algebra_initial_source_protocol_v1_20261009/FIXED_INITIAL_ROSTER_AND_SUBCASES_V1.json \
  --results reviews/evidence/public_live_affine_v2_foundation_algebra_initial_bounded11_runtime_once_v1_20261009/INITIAL_BOUNDED11_GROUP_RESULTS.json \
  --output-dir /tmp/fresh-initial-verification-figure
```

The output directory must be new. Rendering never executes the C++ test program or recomputes research results. Physical admission, live context, first4ms, Model, robot motion and RSS remain outside the run and figure scope.
